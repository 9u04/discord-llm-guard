module.exports = (req, res) => {
  const username = process.env.AUTH_USERNAME || "";
  const password = process.env.AUTH_PASSWORD || "";
  const apiBaseUrl = process.env.API_BASE_URL || "";
  const appTitle = process.env.APP_TITLE || "";

  res.setHeader("Cache-Control", "no-store");
  res.status(200).json({
    auth: { username, password },
    apiBaseUrl,
    appTitle,
  });
};



