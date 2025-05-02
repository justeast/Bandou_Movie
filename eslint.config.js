import globals from "globals";
import pluginJs from "@eslint/js";
import pluginVue from "eslint-plugin-vue";


/** @type {import('eslint').Linter.Config[]} */
export default [
  {files: ["**/*.{js,mjs,cjs,vue}"]},
  {languageOptions: { globals: globals.browser }},
  pluginJs.configs.recommended,
  ...pluginVue.configs["flat/essential"],
  {
    rules:{
      "semi": [0, "always"], // 语句强制分号结尾
      "quotes": [0, "double"], // 引号类型 ""
      "no-alert": 0, // 禁止使用alert
      "no-console": 0, // 禁止使用console
      "no-const-assign": 2, // 禁止修改const声明的变量
      "no-debugger": 2, // 禁止使用debugger
      "no-duplicate-case": 2, // switch中的case标签不能重复
      "no-extra-semi": 2, // 禁止多余的冒号
      "no-multi-spaces": 1, // 不能用多余的空格
      'no-unused-vars': 1, //不能出现未使用变量
      'vue/multi-word-component-names': 0 //要求组件名称始终为多字
    }
  }
];