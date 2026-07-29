import {
  EnvironmentProviders,
  inject,
  InjectionToken,
  makeEnvironmentProviders,
} from "@angular/core";
import {
  HttpInterceptorFn,
  provideHttpClient,
  withInterceptors,
} from "@angular/common/http";

export type FilterxTokenProvider = () => string | null | undefined;

export interface FilterxAuthConfig {
  tokenProvider?: FilterxTokenProvider;
  storageKey?: string;
  scheme?: string;
}

export interface FilterxConfig {
  apiBaseUrl: string;
  apiPrefix: string;
  auth?: FilterxAuthConfig;
  savedFiltersEnabled: boolean;
}

const DEFAULT_CONFIG: FilterxConfig = {
  apiBaseUrl: "",
  apiPrefix: "/api",
  savedFiltersEnabled: true,
};

export const FILTERX_CONFIG = new InjectionToken<FilterxConfig>(
  "FILTERX_CONFIG",
  {
    providedIn: "root",
    factory: () => DEFAULT_CONFIG,
  },
);

export function provideFilterx(
  config: Partial<FilterxConfig> = {},
): EnvironmentProviders {
  return makeEnvironmentProviders([
    {
      provide: FILTERX_CONFIG,
      useValue: { ...DEFAULT_CONFIG, ...config, auth: { ...config.auth } },
    },
    provideHttpClient(withInterceptors([filterxAuthInterceptor])),
  ]);
}

export function joinFilterxUrl(baseUrl: string, endpoint: string): string {
  const base = baseUrl.replace(/\/$/, "");
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${base}${path}`;
}

export const filterxAuthInterceptor: HttpInterceptorFn = (request, next) => {
  const config = inject(FILTERX_CONFIG);
  const targetPrefix = joinFilterxUrl(config.apiBaseUrl, config.apiPrefix);
  if (
    !request.url.startsWith(targetPrefix) ||
    request.headers.has("Authorization")
  ) {
    return next(request);
  }

  let token = config.auth?.tokenProvider?.() ?? null;
  if (
    !token &&
    config.auth?.storageKey &&
    typeof localStorage !== "undefined"
  ) {
    token = localStorage.getItem(config.auth.storageKey);
  }
  if (!token) return next(request);

  const scheme = config.auth?.scheme ?? "Bearer";
  return next(
    request.clone({ setHeaders: { Authorization: `${scheme} ${token}` } }),
  );
};
