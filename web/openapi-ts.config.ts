import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: './openapi.json',
  output: './src/api',
  plugins: [
    '@hey-api/typescript',
    '@hey-api/schemas',
    {
      name: '@hey-api/sdk',
      transformer: true,
      validator: true,
    },
    {
      dates: true,
      name: '@hey-api/transformers',
    },
    '@hey-api/client-axios',
    '@tanstack/react-query',
    'zod',
  ],
});
