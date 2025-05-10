import { useEffect, useState } from "react";
import { IEntityComponent, getProxy } from "@investigativedata/ftmq";
import { IImageAttribution, IImageMeta } from "./types";
import { getImage } from ".";

const DEFAULT_LANG = "en";

interface IComponent extends IEntityComponent {
  readonly api: string;
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
  const entity = getProxy(props.entity);
  // currently, only qid is supported
  const id = entity.getFirst("wikidataId");
  if (!id) return null;

  const [image, setImage] = useState<IImageMeta>();

  useEffect(() => {
    getImage(props.api, id.toString()).then(setImage);
  }, [id]);

  return image ? (
    <span className="ftm-assets__Image-wraper">
      <img
        style={{ width: "100%", height: "auto" }}
        src={props.thumbnail ? image.thumbnail_url : image.url}
        alt={extractAlt(image)}
      />
      <ImageAttribution attribution={image.attribution} />
    </span>
  ) : null;
}
