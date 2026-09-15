package com.example;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController public class HealthController {
  @GetMapping("/health") public Map<String, Boolean> health() { return Map.of("ok", true); }
}
