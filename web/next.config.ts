import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Output standalone for Docker deployment if needed
  // output: "standalone",
  allowedDevOrigins: ["192.168.1.36"],
  typescript: {
    // TODO: Fix Supabase generated type compatibility with @supabase/supabase-js@2.97.0
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
