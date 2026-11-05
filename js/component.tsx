import { useEffect, useState } from "react";
import { IEntityComponent, getProxy } from "@investigativedata/ftmq";
import { IImageAttribution, IImageMeta } from "./types";
import { getImage } from ".";

const DEFAULT_LANG = "en";

interface IComponent extends IEntityComponent {
  readonly root: string; // base url the asset store is served from
  readonly thumbnail?: boolean;
}

const extractAlt = (image: IImageMeta, lang: string = DEFAULT_LANG): string => {
  if (lang) {
    const alt =
      image.alt.find(({ language }) => language == lang) ||
      image.alt.find(({ language }) => language == DEFAULT_LANG);
    if (alt) return alt.text;
  }
  return image.alt[0]?.text || image.name;
};

export function ImageAttribution(props: { attribution: IImageAttribution }) {
  const { license, license_url, author } = props.attribution;
  return (
    <span className="ftm-assets__ImageAttribution">
      <span className="ftm-assets__ImageAttribution__license">
        License: <a href={license_url}>{license}</a>
      </span>
      {author ? (
        <span className="ftm-assets__ImageAttribution__author">
          Author: {author}
        </span>
      ) : null}
    </span>
  );
}

export function EntityImage(props: IComponent) {
  const [image, setImage] = useState<IImageMeta | null>(null);
  const entity = getProxy(props.entity);
  const id = entity.getFirst("wikidataId");

  useEffect(() => {
    // currently, only qid is supported
    id &&
      getImage(props.root, id.toString())
        .then(setImage)
        .catch(() => setImage(null));
  }, [id, props.root]);

  return image ? (
    <span className="ftm-assets__Image-wrapper">
      <img
        src={props.thumbnail ? image.thumbnail_url : image.url}
        alt={extractAlt(image)}
      />
      {image.attribution ? (
        <ImageAttribution attribution={image.attribution} />
      ) : null}
    </span>
  ) : null;
}
