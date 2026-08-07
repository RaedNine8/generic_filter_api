import java.io.IOException;
import java.lang.annotation.Annotation;
import java.lang.reflect.AnnotatedElement;
import java.lang.reflect.Field;
import java.lang.reflect.GenericArrayType;
import java.lang.reflect.Member;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * FilterX's dependency-free, source-launchable JPA reflection helper.
 *
 * It deliberately refers to JPA annotations by runtime name, so it can inspect
 * either javax.persistence or jakarta.persistence projects without compiling
 * against either API. The host's compiled classes and runtime dependencies are
 * supplied on java's class path by the Python scanner.
 */
public final class FilterxJpaScanner {
    public static final String HELPER_VERSION = "0.1.0";
    public static final String PROTOCOL_VERSION = "filterx-ir/v1";

    private static final Set<String> JPA_PREFIXES = Set.of("jakarta.persistence.", "javax.persistence.");
    private static final Set<String> RELATIONSHIPS = Set.of("OneToOne", "OneToMany", "ManyToOne", "ManyToMany");

    private FilterxJpaScanner() {
    }

    public static void main(String[] args) {
        try {
            if (args.length == 1 && args[0].equals("--filterx-helper-version")) {
                System.out.println("{\"helper_version\":\"" + HELPER_VERSION
                        + "\",\"protocol_version\":\"" + PROTOCOL_VERSION + "\"}");
                return;
            }
            Map<String, String> options = options(args);
            String expected = required(options, "helper-version");
            if (!HELPER_VERSION.equals(expected)) {
                fail(4, "FILTERX_HELPER_VERSION_MISMATCH: helper=" + HELPER_VERSION + " package=" + expected);
            }
            Path classesDir = Path.of(required(options, "classes-dir")).toAbsolutePath().normalize();
            if (!Files.isDirectory(classesDir)) {
                fail(3, "FILTERX_CLASSES_MISSING: compiled classes directory does not exist: " + classesDir);
            }
            int maxDepth = Integer.parseInt(options.getOrDefault("max-depth", "3"));
            System.out.println(Json.write(scan(classesDir, maxDepth)));
        } catch (Exit failure) {
            System.err.println(failure.getMessage());
            System.exit(failure.code);
        } catch (Throwable failure) {
            System.err.println(
                    "FILTERX_REFLECTION_FAILED: " + failure.getClass().getSimpleName() + ": " + failure.getMessage());
            System.exit(5);
        }
    }

    private static Map<String, Object> scan(Path classesDir, int maxDepth) throws IOException {
        List<Class<?>> classes = new ArrayList<>();
        try (var paths = Files.walk(classesDir)) {
            for (Path path : paths.filter(item -> item.toString().endsWith(".class")).sorted().toList()) {
                String relative = classesDir.relativize(path).toString().replace('\\', '/');
                if (relative.equals("module-info.class") || relative.endsWith("/package-info.class"))
                    continue;
                String name = relative.substring(0, relative.length() - 6).replace('/', '.');
                try {
                    Class<?> candidate = Class.forName(name, false, Thread.currentThread().getContextClassLoader());
                    if (annotation(candidate, "Entity") != null)
                        classes.add(candidate);
                } catch (ClassNotFoundException | LinkageError failure) {
                    throw new IllegalStateException("cannot load compiled class " + name
                            + "; ensure runtime dependencies are available (" + failure + ")", failure);
                }
            }
        }
        classes.sort(Comparator.comparing(Class::getSimpleName));
        Map<Class<?>, EntityModel> models = new LinkedHashMap<>();
        for (Class<?> type : classes)
            models.put(type, inspect(type));
        Map<String, Set<String>> graph = graph(models);
        List<List<String>> cycles = cycles(graph);
        int graphDepth = maxDepth(graph, maxDepth);

        List<Object> entities = new ArrayList<>();
        for (EntityModel model : models.values()) {
            List<Object> relationships = new ArrayList<>();
            for (RelationshipModel relationship : model.relationships) {
                EntityModel target = models.get(relationship.target);
                if (target == null)
                    continue;
                boolean cycle = reaches(graph, target.name, model.name, new LinkedHashSet<>());
                relationships.add(map(
                        "name", relationship.name,
                        "kind", relationship.kind,
                        "target_entity", target.name,
                        "target_table", target.table,
                        "join_path", List.of(relationship.name),
                        "depth", 1,
                        "collection", relationship.collection,
                        "back_populates", relationship.mappedBy.isBlank() ? null : relationship.mappedBy,
                        "cycle", cycle));
            }
            List<Object> memberships = cycles.stream()
                    .filter(cycle -> cycle.contains(model.name)).map(ArrayList::new)
                    .collect(Collectors.toCollection(ArrayList::new));
            String softDelete = model.fields.stream().map(field -> field.name)
                    .filter(name -> name.equals("deleted_at") || name.equals("is_deleted") || name.equals("deleted"))
                    .findFirst().orElse(null);
            entities.add(map(
                    "name", model.name,
                    "identity", map("module", model.type.getPackageName(), "table", model.table,
                            "primary_keys",
                            model.fields.stream().filter(field -> field.primaryKey).map(field -> field.name).toList()),
                    "fields", model.fields.stream().map(FieldModel::toIr).toList(),
                    "relationships", relationships,
                    "cycle_memberships", memberships,
                    "soft_delete", map("respected", false, "field", softDelete)));
        }
        return map(
                "version", PROTOCOL_VERSION,
                "source_framework", "jpa",
                "entities", entities,
                "routes", List.of(),
                "security", map("identity", null, "row_predicates", List.of(),
                        "entity_row_predicates", List.of(), "field_visibility", null),
                "max_relationship_depth", graphDepth);
    }

    private static EntityModel inspect(Class<?> type) {
        String entityName = stringValue(annotation(type, "Entity"), "name", type.getSimpleName());
        if (entityName.isBlank())
            entityName = type.getSimpleName();
        String table = stringValue(annotation(type, "Table"), "name", entityName);
        if (table.isBlank())
            table = entityName;
        boolean propertyAccess = allMethods(type).stream()
                .anyMatch(method -> annotation(method, "Id") != null || annotation(method, "EmbeddedId") != null);
        List<PersistentMember> members = propertyAccess ? propertyMembers(type) : fieldMembers(type);
        List<FieldModel> fields = new ArrayList<>();
        List<RelationshipModel> relationships = new ArrayList<>();
        for (PersistentMember member : members) {
            Annotation relationship = RELATIONSHIPS.stream().map(name -> annotation(member.element, name))
                    .filter(item -> item != null).findFirst().orElse(null);
            if (relationship != null) {
                String kind = relationship.annotationType().getSimpleName().replaceAll("([a-z])([A-Z])", "$1-$2")
                        .toLowerCase(Locale.ROOT);
                boolean collection = Collection.class.isAssignableFrom(member.rawType);
                Class<?> target = collection ? genericClass(member.genericType) : member.rawType;
                relationships.add(new RelationshipModel(member.name, kind, target, collection,
                        stringValue(relationship, "mappedBy", "")));
                continue;
            }
            if (annotation(member.element, "Transient") != null)
                continue;
            fields.add(field(member));
        }
        fields.sort(Comparator.comparing(field -> field.name));
        relationships.sort(Comparator.comparing(relationship -> relationship.name));
        return new EntityModel(type, entityName, table, fields, relationships);
    }

    private static FieldModel field(PersistentMember member) {
        boolean primaryKey = annotation(member.element, "Id") != null
                || annotation(member.element, "EmbeddedId") != null;
        Annotation column = annotation(member.element, "Column");
        Annotation basic = annotation(member.element, "Basic");
        boolean nullable = !member.rawType.isPrimitive() && !primaryKey
                && booleanValue(column, "nullable", true) && booleanValue(basic, "optional", true);
        boolean unique = booleanValue(column, "unique", false);
        boolean hasDefault = annotation(member.element, "GeneratedValue") != null
                || annotationNamed(member.element, "org.hibernate.annotations.ColumnDefault") != null
                || annotationNamed(member.element, "org.hibernate.annotations.CreationTimestamp") != null
                || annotationNamed(member.element, "org.hibernate.annotations.UpdateTimestamp") != null
                || stringValue(column, "columnDefinition", "").toLowerCase(Locale.ROOT).contains("default");
        String type = fieldType(member.rawType);
        List<String> enumValues = member.rawType.isEnum()
                ? Arrays.stream(member.rawType.getEnumConstants()).map(Object::toString).sorted().toList()
                : List.of();
        return new FieldModel(member.name, type, member.rawType.getTypeName(), nullable, primaryKey,
                unique, hasDefault, operations(type), enumValues);
    }

    private static List<PersistentMember> fieldMembers(Class<?> type) {
        List<PersistentMember> result = new ArrayList<>();
        for (Class<?> current = type; current != null && current != Object.class; current = current.getSuperclass()) {
            for (Field field : current.getDeclaredFields()) {
                if (field.isSynthetic() || Modifier.isStatic(field.getModifiers()))
                    continue;
                result.add(new PersistentMember(field.getName(), field.getType(), field.getGenericType(), field));
            }
        }
        return deduplicate(result);
    }

    private static List<PersistentMember> propertyMembers(Class<?> type) {
        List<PersistentMember> result = new ArrayList<>();
        for (Method method : allMethods(type)) {
            if (Modifier.isStatic(method.getModifiers()) || method.getParameterCount() != 0 || method.isSynthetic())
                continue;
            String name = propertyName(method);
            if (name == null || name.equals("class"))
                continue;
            result.add(new PersistentMember(name, method.getReturnType(), method.getGenericReturnType(), method));
        }
        return deduplicate(result);
    }

    private static List<Method> allMethods(Class<?> type) {
        List<Method> methods = new ArrayList<>();
        for (Class<?> current = type; current != null && current != Object.class; current = current.getSuperclass()) {
            methods.addAll(Arrays.asList(current.getDeclaredMethods()));
        }
        return methods;
    }

    private static List<PersistentMember> deduplicate(List<PersistentMember> values) {
        Map<String, PersistentMember> byName = new LinkedHashMap<>();
        values.stream().sorted(Comparator.comparing(value -> value.name))
                .forEach(value -> byName.putIfAbsent(value.name, value));
        return new ArrayList<>(byName.values());
    }

    private static String propertyName(Method method) {
        String name = method.getName();
        if (name.startsWith("get") && name.length() > 3)
            return decapitalize(name.substring(3));
        if (name.startsWith("is") && name.length() > 2
                && (method.getReturnType() == boolean.class || method.getReturnType() == Boolean.class))
            return decapitalize(name.substring(2));
        return null;
    }

    private static String decapitalize(String value) {
        if (value.length() > 1 && Character.isUpperCase(value.charAt(0)) && Character.isUpperCase(value.charAt(1)))
            return value;
        return Character.toLowerCase(value.charAt(0)) + value.substring(1);
    }

    private static Class<?> genericClass(Type type) {
        if (type instanceof ParameterizedType parameterized) {
            Type[] arguments = parameterized.getActualTypeArguments();
            if (arguments.length > 0) {
                if (arguments[0] instanceof Class<?> value)
                    return value;
                if (arguments[0] instanceof ParameterizedType nested && nested.getRawType() instanceof Class<?> value)
                    return value;
            }
        }
        if (type instanceof GenericArrayType)
            return Object[].class;
        return Object.class;
    }

    private static Map<String, Set<String>> graph(Map<Class<?>, EntityModel> models) {
        Map<String, Set<String>> graph = new LinkedHashMap<>();
        for (EntityModel model : models.values()) {
            Set<String> targets = model.relationships.stream().map(item -> models.get(item.target))
                    .filter(item -> item != null).map(item -> item.name)
                    .collect(Collectors.toCollection(LinkedHashSet::new));
            graph.put(model.name, targets);
        }
        return graph;
    }

    private static List<List<String>> cycles(Map<String, Set<String>> graph) {
        Set<String> canonical = new LinkedHashSet<>();
        List<List<String>> result = new ArrayList<>();
        for (String start : graph.keySet())
            findCycles(start, start, graph, new ArrayList<>(), canonical, result);
        result.sort(Comparator.comparing(cycle -> String.join("/", cycle)));
        return result;
    }

    private static void findCycles(String start, String current, Map<String, Set<String>> graph,
            List<String> path, Set<String> canonical, List<List<String>> result) {
        if (path.contains(current))
            return;
        path.add(current);
        for (String target : graph.getOrDefault(current, Set.of())) {
            if (target.equals(start)) {
                List<String> cycle = new ArrayList<>(path);
                cycle.add(start);
                List<String> body = new ArrayList<>(path);
                int minimum = 0;
                for (int i = 1; i < body.size(); i++)
                    if (body.get(i).compareTo(body.get(minimum)) < 0)
                        minimum = i;
                Collections.rotate(body, -minimum);
                String key = String.join("/", body);
                if (canonical.add(key)) {
                    body.add(body.get(0));
                    result.add(body);
                }
            } else if (!path.contains(target)) {
                findCycles(start, target, graph, path, canonical, result);
            }
        }
        path.remove(path.size() - 1);
    }

    private static boolean reaches(Map<String, Set<String>> graph, String current, String target, Set<String> seen) {
        if (current.equals(target))
            return true;
        if (!seen.add(current))
            return false;
        return graph.getOrDefault(current, Set.of()).stream().anyMatch(next -> reaches(graph, next, target, seen));
    }

    private static int maxDepth(Map<String, Set<String>> graph, int limit) {
        int depth = 0;
        for (String node : graph.keySet())
            depth = Math.max(depth, depth(node, graph, new LinkedHashSet<>(), limit));
        return depth;
    }

    private static int depth(String node, Map<String, Set<String>> graph, Set<String> path, int limit) {
        if (path.size() >= limit)
            return path.size();
        if (!path.add(node))
            return Math.max(0, path.size() - 1);
        int maximum = path.size() - 1;
        for (String next : graph.getOrDefault(node, Set.of()))
            maximum = Math.max(maximum, depth(next, graph, new LinkedHashSet<>(path), limit));
        return maximum;
    }

    private static String fieldType(Class<?> type) {
        if (type.isEnum())
            return "enum";
        if (type == boolean.class || type == Boolean.class)
            return "boolean";
        if (type == byte.class || type == short.class || type == int.class || type == long.class
                || type == Byte.class || type == Short.class || type == Integer.class || type == Long.class
                || type == BigInteger.class)
            return "integer";
        if (type == float.class || type == double.class || type == Float.class || type == Double.class
                || type == BigDecimal.class)
            return "decimal";
        if (type == LocalDate.class || type == java.sql.Date.class)
            return "date";
        if (type == Date.class || type == LocalDateTime.class || type == OffsetDateTime.class
                || type == ZonedDateTime.class
                || type == java.sql.Timestamp.class || type == java.time.Instant.class)
            return "datetime";
        if (type == UUID.class)
            return "uuid";
        if (type == byte[].class || type == Byte[].class)
            return "binary";
        if (Map.class.isAssignableFrom(type) || type.getName().contains("Json"))
            return "json/blob";
        return "string";
    }

    private static List<String> operations(String type) {
        return switch (type) {
            case "integer", "decimal", "date", "datetime" ->
                List.of("eq", "neq", "gt", "gte", "lt", "lte", "in", "not_in", "is_null");
            case "string" ->
                List.of("eq", "neq", "contains", "icontains", "starts_with", "ends_with", "in", "not_in", "is_null");
            case "enum", "uuid", "boolean" -> List.of("eq", "neq", "in", "not_in", "is_null");
            default -> List.of("eq", "neq", "is_null");
        };
    }

    private static Annotation annotation(AnnotatedElement element, String simpleName) {
        for (String prefix : JPA_PREFIXES) {
            Annotation found = annotationNamed(element, prefix + simpleName);
            if (found != null)
                return found;
        }
        return null;
    }

    private static Annotation annotationNamed(AnnotatedElement element, String name) {
        for (Annotation annotation : element.getAnnotations())
            if (annotation.annotationType().getName().equals(name))
                return annotation;
        return null;
    }

    private static Object annotationValue(Annotation annotation, String name, Object fallback) {
        if (annotation == null)
            return fallback;
        try {
            return annotation.annotationType().getMethod(name).invoke(annotation);
        } catch (ReflectiveOperationException failure) {
            return fallback;
        }
    }

    private static String stringValue(Annotation annotation, String name, String fallback) {
        Object value = annotationValue(annotation, name, fallback);
        return value instanceof String text ? text : fallback;
    }

    private static boolean booleanValue(Annotation annotation, String name, boolean fallback) {
        Object value = annotationValue(annotation, name, fallback);
        return value instanceof Boolean flag ? flag : fallback;
    }

    private static Map<String, String> options(String[] args) {
        Map<String, String> result = new LinkedHashMap<>();
        for (int index = 0; index < args.length; index += 2) {
            if (!args[index].startsWith("--") || index + 1 >= args.length)
                fail(2, "Invalid helper arguments.");
            result.put(args[index].substring(2), args[index + 1]);
        }
        return result;
    }

    private static String required(Map<String, String> options, String name) {
        String value = options.get(name);
        if (value == null || value.isBlank())
            fail(2, "Missing --" + name + ".");
        return value;
    }

    private static void fail(int code, String message) {
        throw new Exit(code, message);
    }

    private static Map<String, Object> map(Object... values) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int index = 0; index < values.length; index += 2)
            result.put((String) values[index], values[index + 1]);
        return result;
    }

    private record PersistentMember(String name, Class<?> rawType, Type genericType, AnnotatedElement element) {
    }

    private record RelationshipModel(String name, String kind, Class<?> target, boolean collection, String mappedBy) {
    }

    private record EntityModel(Class<?> type, String name, String table, List<FieldModel> fields,
            List<RelationshipModel> relationships) {
    }

    private record FieldModel(String name, String type, String sourceType, boolean nullable, boolean primaryKey,
            boolean unique, boolean hasDefault, List<String> operations, List<String> enumValues) {
        Map<String, Object> toIr() {
            return map("name", name, "type", type, "source_type", sourceType, "nullable", nullable,
                    "primary_key", primaryKey, "unique", unique, "has_default", hasDefault,
                    "foreign_keys", List.of(), "operations", operations, "enum_values", enumValues,
                    "visibility", "public", "permission", null);
        }
    }

    private static final class Exit extends RuntimeException {
        final int code;

        Exit(int code, String message) {
            super(message);
            this.code = code;
        }
    }

    private static final class Json {
        static String write(Object value) {
            if (value == null)
                return "null";
            if (value instanceof String text)
                return quote(text);
            if (value instanceof Boolean || value instanceof Number)
                return value.toString();
            if (value instanceof Map<?, ?> map)
                return map.entrySet().stream()
                        .map(entry -> quote(entry.getKey().toString()) + ":" + write(entry.getValue()))
                        .collect(Collectors.joining(",", "{", "}"));
            if (value instanceof Iterable<?> items) {
                List<String> values = new ArrayList<>();
                for (Object item : items)
                    values.add(write(item));
                return String.join(",", values).transform(text -> "[" + text + "]");
            }
            return quote(value.toString());
        }

        private static String quote(String value) {
            StringBuilder result = new StringBuilder("\"");
            for (char character : value.toCharArray()) {
                switch (character) {
                    case '\\' -> result.append("\\\\");
                    case '"' -> result.append("\\\"");
                    case '\n' -> result.append("\\n");
                    case '\r' -> result.append("\\r");
                    case '\t' -> result.append("\\t");
                    default -> {
                        if (character < 0x20)
                            result.append(String.format("\\u%04x", (int) character));
                        else
                            result.append(character);
                    }
                }
            }
            return result.append('"').toString();
        }
    }
}
