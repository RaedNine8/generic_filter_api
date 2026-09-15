package com.example;

import com.example.filterx.generated.FilterxSecurity;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class FixtureSecurityConfiguration {
 @Bean FilterxSecurity.IdentityExtractor identity(){ return request -> request.getHeader("x-genre") == null ? "Tech" : request.getHeader("x-genre"); }
 @Bean FilterxSecurity.RowLevelSecurity rows(){ return (principal,entity,action,request) -> "Book".equals(entity.path("name").asText()) ? (root,query,cb) -> cb.equal(root.get("genre"),principal) : null; }
 @Bean FilterxSecurity.FieldVisibility fields(){ return (principal,entity,field,action,request) -> !"price".equals(field); }
}
