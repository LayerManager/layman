const crypto = require('crypto')
const http = require("http");
const https = require("https");
const express = require("express");
const path = require("path");
const {createProxyMiddleware} = require('http-proxy-middleware');

const port = process.env.PORT || 8080;

const app = express();

const proxyRouter = (req) => {
  const requested_url = new URL(req.query.url);
  return requested_url.origin; // protocol + domain + port
};

const pathRewrite = (path, req) => {
  const requested_url = new URL(req.query.url);
  const requested_path = `${requested_url.pathname}${requested_url.search}${requested_url.hash}`
  return requested_path;  // path + query parameters + hash
}

const onProxyRes = (proxyRes, req, res) => {
  const headers = proxyRes.headers;
  const status_code = proxyRes.statusCode;
  let msg = `onProxyRes, status=${status_code}`
  if(status_code !== 200) {
    msg += `, headers=${JSON.stringify(headers, null, 2)}`;
  }
  console.log(msg + '\n')
}

const httpProxyMiddleware = createProxyMiddleware({
  router: proxyRouter,
  pathRewrite,
  onProxyReq: (proxyReq, req, res) => {
    const full_url = proxyReq.protocol + '//' + proxyReq.host + proxyReq.path;
    const headers = proxyReq.getHeaders();
    console.log(`onProxyReq, full_url=${full_url}, headers=${JSON.stringify(headers, null, 2)}`)
  },
  onProxyRes: onProxyRes,
  changeOrigin: true,
  secure: false,
  // logLevel: "debug",
});

const httpsProxyMiddleware = createProxyMiddleware({
  router: proxyRouter,
  pathRewrite,
  onProxyReq: (proxyReq, req, res) => {
    const full_url = proxyReq.protocol + '//' + proxyReq.host + proxyReq.path;
    const headers = proxyReq.getHeaders();
    proxyReq.agent = new https.Agent({
      // see https://github.com/LayerManager/layman/issues/755
      secureOptions: crypto.constants.SSL_OP_LEGACY_SERVER_CONNECT,
    });
    console.log(`onProxyReq, full_url=${full_url}, headers=${JSON.stringify(headers, null, 2)}`)
  },
  onProxyRes: onProxyRes,
  changeOrigin: true,
  secure: false,
  // logLevel: "debug",
});

app.use("/http_proxy", httpProxyMiddleware);
app.use("/https_proxy", httpsProxyMiddleware);

app.use("/", express.static(path.join(__dirname, "dist")));

app.listen(port, () => {
  console.log();
  console.log(`  App running in port ${port}`);
  console.log();
  console.log(`  > Local: \x1b[36mhttp://localhost:\x1b[1m${port}/\x1b[0m`);
});