from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from typing import Any

from tree_sitter import Language, Node, Parser
import tree_sitter_groovy
import tree_sitter_kotlin


_MAVEN_DEPENDENCY_KEYS = (
    "group_id",
    "artifact_id",
    "version",
    "scope",
    "type",
    "classifier",
    "optional",
)


def render_maven_merge(original: str, payload: Mapping[str, Any]) -> str:
    """Merge Maven properties/dependencies using ElementTree.

    Payload shape::

        {"properties": {"name": "value"},
         "dependencies": [{"group_id": "g", "artifact_id": "a",
                            "version": "1", "scope": "runtime", ...}]}
    """
    if not original.strip():
        raise ValueError("Maven structured merge requires an existing pom.xml document.")
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.fromstring(original, parser=parser)
    if _local_name(root.tag) != "project":
        raise ValueError("Maven structured merge requires a <project> document root.")

    namespace = _namespace(root.tag)
    if namespace:
        ET.register_namespace("", namespace)

    properties_payload = payload.get("properties", {})
    dependencies_payload = payload.get("dependencies", [])
    if not isinstance(properties_payload, Mapping):
        raise ValueError("Maven merge 'properties' must be an object.")
    if not _is_sequence(dependencies_payload):
        raise ValueError("Maven merge 'dependencies' must be a list.")

    changed = False
    if properties_payload:
        properties = _direct_child(root, "properties")
        if properties is None:
            properties = ET.SubElement(root, _qualified(namespace, "properties"))
            changed = True
        existing_properties = {
            _local_name(child.tag): child for child in properties if isinstance(child.tag, str)
        }
        for name in sorted(properties_payload):
            value = properties_payload[name]
            if not isinstance(name, str) or not name or not isinstance(value, (str, int, float, bool)):
                raise ValueError("Maven property names and values must be scalar values.")
            text = str(value).lower() if isinstance(value, bool) else str(value)
            node = existing_properties.get(name)
            if node is None:
                node = ET.SubElement(properties, _qualified(namespace, name))
                node.text = text
                changed = True
            elif (node.text or "") != text:
                node.text = text
                changed = True

    normalized_dependencies = [_normalize_maven_dependency(item) for item in dependencies_payload]
    if normalized_dependencies:
        dependencies = _direct_child(root, "dependencies")
        if dependencies is None:
            dependencies = ET.SubElement(root, _qualified(namespace, "dependencies"))
            changed = True
        existing = {
            (
                _child_text(item, "groupId"),
                _child_text(item, "artifactId"),
                _child_text(item, "type"),
                _child_text(item, "classifier"),
            )
            for item in dependencies
            if isinstance(item.tag, str) and _local_name(item.tag) == "dependency"
        }
        for item in sorted(
            normalized_dependencies,
            key=lambda value: (
                value["group_id"],
                value["artifact_id"],
                value.get("type", ""),
                value.get("classifier", ""),
            ),
        ):
            identity = (
                item["group_id"],
                item["artifact_id"],
                item.get("type", ""),
                item.get("classifier", ""),
            )
            if identity in existing:
                continue
            dependency = ET.SubElement(dependencies, _qualified(namespace, "dependency"))
            for payload_key, xml_name in (
                ("group_id", "groupId"),
                ("artifact_id", "artifactId"),
                ("version", "version"),
                ("scope", "scope"),
                ("type", "type"),
                ("classifier", "classifier"),
                ("optional", "optional"),
            ):
                if payload_key not in item:
                    continue
                child = ET.SubElement(dependency, _qualified(namespace, xml_name))
                child.text = str(item[payload_key]).lower() if isinstance(item[payload_key], bool) else str(item[payload_key])
            existing.add(identity)
            changed = True

    unknown = set(payload) - {"properties", "dependencies"}
    if unknown:
        raise ValueError(f"Unsupported Maven merge keys: {', '.join(sorted(unknown))}.")
    if not changed:
        return original

    ET.indent(root, space="  ")
    declaration = original.lstrip().startswith("<?xml")
    stream = io.BytesIO()
    ET.ElementTree(root).write(stream, encoding="utf-8", xml_declaration=declaration, short_empty_elements=True)
    newline = "\r\n" if "\r\n" in original else "\n"
    return stream.getvalue().decode("utf-8").replace("\n", newline) + newline


def render_gradle_merge(original: str, payload: Mapping[str, Any], *, kotlin_dsl: bool) -> str:
    """Merge Gradle dependency declarations after validating and locating blocks via tree-sitter.

    Payload shape::

        {"dependencies": [{"configuration": "implementation",
                            "group": "g", "name": "a", "version": "1"}]}

    ``notation`` may replace group/name/version for platform/project/file notations.
    """
    unknown = set(payload) - {"dependencies"}
    if unknown:
        raise ValueError(f"Unsupported Gradle merge keys: {', '.join(sorted(unknown))}.")
    dependencies_payload = payload.get("dependencies", [])
    if not _is_sequence(dependencies_payload):
        raise ValueError("Gradle merge 'dependencies' must be a list.")
    normalized = [_normalize_gradle_dependency(item) for item in dependencies_payload]

    source = original.encode("utf-8")
    language = Language(tree_sitter_kotlin.language() if kotlin_dsl else tree_sitter_groovy.language())
    tree = Parser(language).parse(source)
    if tree.root_node.has_error:
        dialect = "Kotlin" if kotlin_dsl else "Groovy"
        raise ValueError(f"Gradle {dialect} DSL document contains syntax errors.")

    block = _find_top_level_gradle_block(tree.root_node, source, "dependencies", kotlin_dsl)
    existing = _gradle_dependencies(block, source, kotlin_dsl) if block is not None else set()
    additions = [item for item in sorted(normalized, key=_gradle_dependency_sort_key) if _gradle_identity(item) not in existing]
    if not additions:
        return original

    newline = "\r\n" if "\r\n" in original else "\n"
    rendered_lines = [_render_gradle_dependency(item, kotlin_dsl) for item in additions]
    if block is None:
        prefix = "" if not original or original.endswith(("\n", "\r")) else newline
        body = newline.join(f"    {line}" for line in rendered_lines)
        return f"{original}{prefix}dependencies {{{newline}{body}{newline}}}{newline}"

    close_byte = block.end_byte - 1
    if source[close_byte:block.end_byte] != b"}":
        raise ValueError("tree-sitter did not identify a valid Gradle dependencies block.")
    line_start = source.rfind(b"\n", 0, close_byte) + 1
    close_indent = source[line_start:close_byte].decode("utf-8")
    if close_indent.strip():
        close_indent = ""
    child_indent = close_indent + "    "
    insertion = "".join(f"{child_indent}{line}{newline}" for line in rendered_lines)
    before = source[:close_byte].decode("utf-8")
    after = source[close_byte:].decode("utf-8")
    if before and not before.endswith(("\n", "\r")):
        insertion = newline + insertion
    return before + insertion + after


def _normalize_maven_dependency(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("Each Maven dependency must be an object.")
    unknown = set(value) - set(_MAVEN_DEPENDENCY_KEYS)
    if unknown:
        raise ValueError(f"Unsupported Maven dependency keys: {', '.join(sorted(unknown))}.")
    normalized = dict(value)
    for required in ("group_id", "artifact_id"):
        if not isinstance(normalized.get(required), str) or not normalized[required].strip():
            raise ValueError(f"Maven dependency '{required}' must be a non-empty string.")
    for key, item in normalized.items():
        if key == "optional":
            if not isinstance(item, bool):
                raise ValueError("Maven dependency 'optional' must be boolean.")
        elif not isinstance(item, str) or not item.strip():
            raise ValueError(f"Maven dependency '{key}' must be a non-empty string.")
    return normalized


def _normalize_gradle_dependency(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("Each Gradle dependency must be an object.")
    unknown = set(value) - {"configuration", "group", "name", "version", "notation"}
    if unknown:
        raise ValueError(f"Unsupported Gradle dependency keys: {', '.join(sorted(unknown))}.")
    normalized = {str(key): item for key, item in value.items()}
    configuration = normalized.get("configuration")
    if not isinstance(configuration, str) or not configuration.strip() or not configuration.replace("_", "").isalnum():
        raise ValueError("Gradle dependency 'configuration' must be an identifier.")
    notation = normalized.get("notation")
    coordinate_keys = {key for key in ("group", "name", "version") if key in normalized}
    if notation is not None:
        if coordinate_keys:
            raise ValueError("Gradle dependency must use either 'notation' or group/name/version, not both.")
        if not isinstance(notation, str) or not notation.strip():
            raise ValueError("Gradle dependency 'notation' must be a non-empty string.")
    else:
        if coordinate_keys not in ({"group", "name"}, {"group", "name", "version"}):
            raise ValueError("Gradle dependency requires group and name; version is optional for BOM-managed dependencies.")
        if any(not isinstance(normalized[key], str) or not normalized[key].strip() for key in coordinate_keys):
            raise ValueError("Gradle dependency coordinates must be non-empty strings.")
    return normalized  # type: ignore[return-value]


def _find_top_level_gradle_block(root: Node, source: bytes, name: str, kotlin_dsl: bool) -> Node | None:
    for statement in root.named_children:
        call = statement
        if not kotlin_dsl and statement.type == "expression_statement" and statement.named_children:
            call = statement.named_children[0]
        if call.type not in {"call_expression", "method_invocation"}:
            continue
        identifier = call.child_by_field_name("name")
        if identifier is None and call.named_children:
            identifier = call.named_children[0]
        if identifier is None or _node_text(identifier, source) != name:
            continue
        wanted = "lambda_literal" if kotlin_dsl else "closure"
        block = _first_descendant(call, wanted)
        if block is not None:
            return block
    return None


def _gradle_dependencies(block: Node, source: bytes, kotlin_dsl: bool) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    if block is None:
        return found
    for node in _descendants(block):
        if node.type not in {"call_expression", "method_invocation", "juxt_function_call"}:
            continue
        identifier = node.child_by_field_name("name")
        if identifier is None and node.named_children:
            identifier = node.named_children[0]
        if identifier is None or identifier.type != "identifier":
            continue
        configuration = _node_text(identifier, source)
        literal = next(
            (
                _literal_value(child, source)
                for child in _descendants(node)
                if child.type in {"string_literal", "character_literal"}
            ),
            None,
        )
        if literal is not None:
            found.add((configuration, literal))
    return found


def _render_gradle_dependency(item: Mapping[str, str], kotlin_dsl: bool) -> str:
    notation = item.get("notation") or _gradle_coordinate(item)
    escaped = notation.replace("\\", "\\\\").replace('"', '\\"')
    if kotlin_dsl:
        return f'{item["configuration"]}("{escaped}")'
    return f'{item["configuration"]} "{escaped}"'


def _gradle_identity(item: Mapping[str, str]) -> tuple[str, str]:
    notation = item.get("notation") or _gradle_coordinate(item)
    return item["configuration"], notation


def _gradle_coordinate(item: Mapping[str, str]) -> str:
    coordinate = f"{item['group']}:{item['name']}"
    return f"{coordinate}:{item['version']}" if item.get("version") else coordinate


def _gradle_dependency_sort_key(item: Mapping[str, str]) -> tuple[str, str]:
    return _gradle_identity(item)


def _literal_value(node: Node, source: bytes) -> str:
    text = _node_text(node, source)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return bytes(text[1:-1], "utf-8").decode("unicode_escape")
    return text


def _descendants(node: Node):
    stack = list(reversed(node.named_children))
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.named_children))


def _first_descendant(node: Node, node_type: str) -> Node | None:
    return next((child for child in _descendants(node) if child.type == node_type), None)


def _node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _namespace(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def _qualified(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}" if namespace else name


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _direct_child(parent: ET.Element, name: str) -> ET.Element | None:
    return next(
        (child for child in parent if isinstance(child.tag, str) and _local_name(child.tag) == name),
        None,
    )


def _child_text(parent: ET.Element, name: str) -> str:
    child = _direct_child(parent, name)
    return (child.text or "").strip() if child is not None else ""
