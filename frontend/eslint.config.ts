import globals from 'globals'
import pluginVue from 'eslint-plugin-vue'
import pluginPrettierRecommended from 'eslint-plugin-prettier/recommended'
import tseslint from 'typescript-eslint'
import type { Linter } from 'eslint'

export default [
  {
    ignores: [
      'node_modules/',
      'dist/',
      'coverage/',
      'public/',
      '*.config.js',
      '*.config.ts',
      'vite.config.ts',
      'eslint.config.ts'
    ]
  },

  ...tseslint.configs.recommended,

  ...pluginVue.configs['flat/recommended'],

  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: ['.vue']
      }
    }
  },

  {
    files: ['**/*.{ts,tsx,js,mjs,cjs}'],

    languageOptions: {
      globals: globals.browser
    },

    rules: {
      eqeqeq: ['error', 'always'],

      'no-console': ['warn', { allow: ['warn', 'error'] }],

      'no-debugger': 'error',

      '@typescript-eslint/no-unused-vars': 'warn',

      '@typescript-eslint/no-explicit-any': 'warn',

      '@typescript-eslint/explicit-module-boundary-types': 'off'
    }
  },

  {
    files: ['**/*.vue'],

    rules: {
      'vue/multi-word-component-names': 'off',

      'vue/no-v-html': 'off',

      'vue/require-default-prop': 'off',

      'vue/block-order': [
        'error',
        {
          order: ['script', 'template', 'style']
        }
      ],

      'vue/max-attributes-per-line': [
        'error',
        {
          singleline: 3,
          multiline: 1
        }
      ]
    }
  },

  pluginPrettierRecommended
] satisfies Linter.Config[]
