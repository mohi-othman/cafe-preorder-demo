import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone", // self-contained server for the Docker image (src/web/Dockerfile)
  cacheComponents: true,
  partialPrefetching: true,
};

export default nextConfig;
