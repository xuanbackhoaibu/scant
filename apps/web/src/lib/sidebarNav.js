export function isSidebarItemActive(pathname, href) {
  if (!pathname || !href) return false;
  if (href === "/") return pathname === "/";
  if (pathname === href) return true;

  if (href === "/projects") {
    return pathname.startsWith("/projects/") && !pathname.startsWith("/projects/new");
  }

  return pathname.startsWith(`${href}/`);
}
