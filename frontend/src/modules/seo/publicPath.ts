export function listingIdFromPath(pathname: string): number | null {
  const match = (pathname.split("?")[0] || "").match(/^\/listings\/(\d+)\/?$/);
  return match ? Number(match[1]) : null;
}

export function sellerIdFromPath(pathname: string): number | null {
  const match = (pathname.split("?")[0] || "").match(/^\/sellers\/(\d+)\/?$/);
  return match ? Number(match[1]) : null;
}

export function isPublicSeoPath(pathname: string): boolean {
  const path = pathname.split("?")[0] || "/";
  if (path === "/" || path === "") {
    return true;
  }
  return listingIdFromPath(path) !== null || sellerIdFromPath(path) !== null;
}
