package com.example;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration public class HostSecurityConfiguration {
  @Bean SecurityFilterChain permitAll(HttpSecurity http) throws Exception {
    return http.securityMatcher("/health").csrf(c -> c.disable()).authorizeHttpRequests(a -> a.anyRequest().permitAll()).build();
  }
}
