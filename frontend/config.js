export const APP_CONFIG = {
  appTitle: "Discord LLM Guard 控制台",
  auth: {
    username: "admin",
    password: "",
  },
  apiBaseUrl: "",
};

if (typeof window !== "undefined" && window.APP_CONFIG_OVERRIDE) {
  const override = window.APP_CONFIG_OVERRIDE;
  APP_CONFIG.appTitle = override.appTitle ?? APP_CONFIG.appTitle;
  APP_CONFIG.apiBaseUrl = override.apiBaseUrl ?? APP_CONFIG.apiBaseUrl;
  APP_CONFIG.auth = {
    ...APP_CONFIG.auth,
    ...(override.auth ?? {}),
  };
}

