export const yuan = (value) => {
  if (value === null || value === undefined || value === '') return '¥0.00'
  // 后端金额已经是保留两位小数的字符串，这里只做展示拼接，不做浮点运算
  return `¥${value}`
}

export const dateTime = (value) => (value ? String(value).replace('T', ' ').slice(0, 19) : '—')

/**
 * 图文详情由管理员填写，直接 v-html 会把任意脚本注入页面，
 * 因此这里剥掉标签按纯文本展示。
 */
export const plainText = (html) =>
  String(html ?? '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
