export interface IImageAttribution {
  readonly license: string;
  readonly license_url: string;
  readonly author?: string | null;
  readonly source?: string | null;
  readonly source_url?: string | null;
}

export interface IImageAlt {
  readonly text: string;
  readonly language?: string;
}

export interface IImageMeta {
  readonly id: string;
  readonly name: string;
  readonly sha256?: string | null;
  readonly url: string;
  readonly thumbnail_url: string;
  readonly original_url?: string | null;
  readonly alt: IImageAlt[];
  readonly attribution?: IImageAttribution | null;
}
