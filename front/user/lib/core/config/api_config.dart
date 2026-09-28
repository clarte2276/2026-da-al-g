String defaultApiBaseUrl() {
  const configured = String.fromEnvironment('API_BASE_URL');
  if (configured.trim().isNotEmpty) {
    return configured.trim().replaceAll(RegExp(r'/+$'), '');
  }
  return 'https://2026-da-al-g-production.up.railway.app';
}
