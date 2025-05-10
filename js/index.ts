import { IImageMeta } from "./types";

export * from "./component";
export * from "./types";

const makeMetaUrl = (api: string, id: string): string => `${api}/img/${id}`;

export const getImage = async (
  api: string,
  id: string,
  opts: RequestInit = {},
): Promise<IImageMeta> =>
  fetcher(makeMetaUrl(api, id), opts) as Promise<IImageMeta>;

async function fetcher(url: string, opts: RequestInit = {}): Promise<any> {
  const res = await fetch(url, opts);
  if (res.ok) {
    const data = await res.json();
    return data;
  }
  throw new Error(`Fetch error: ${res.status} ${res.statusText}`);
}
