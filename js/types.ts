export interface IImageAttribution {
  readonly license: string;
  readonly license_url: string;
  readonly author?: string;
}

export interface IImageAlt {
  readonly text: string;
  readonly language?: string;
}

export interface IImageMeta {
  readonly id: string;
  readonly name: string;
  readonly url: string;
  readonly original_url: string;
  readonly thumbnail_url: string;
  readonly alt: IImageAlt[];
  readonly attribution: IImageAttribution;
}
