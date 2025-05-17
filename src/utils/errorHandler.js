export const getErrorMessage = (error) => {
  const status = error.response?.status;
  const data = error.response?.data;

  // 首先检查是否有错误信息，优先使用后端返回的error字段
  if (data?.error) return data.error;

  // 然后检查detail字段
  if (data?.detail) return data.detail;

  if (data?.detail) return data.detail;
  if (status === 401) return "登录已过期，请重新登录";
  if (status === 403) return "权限不足";
  if (status === 413) return "文件大小超过限制";
  if (status >= 500) return "服务器繁忙，请稍后再试";

  return error.message || "请求失败，请检查网络";
};
