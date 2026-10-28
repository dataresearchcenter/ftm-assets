import { IImageMeta } from "./types";

export * from "./component";
export * from "./types";

const makeMetaUrl = (root: string, id: string): string =>
  `${root}/img/${id}/meta.json`;

// urls in meta.json are relative to its location
const resolveUrl = (url: string, base: string): string =>
  new URL(url, base).toString();

export const getImage = async (
  root: string,
  id: string,
  opts: RequestInit = {},
): Promise<IImageMeta> => {
  const res = await fetch(makeMetaUrl(root, id), opts);
  if (!res.ok) {
    throw new Error(`Fetch error: ${res.status} ${res.statusText}`);
  }
  const image: IImageMeta = await res.json();
  return {
    ...image,
    url: resolveUrl(image.url, res.url),
    thumbnail_url: resolveUrl(image.thumbnail_url, res.url),
  };
};
