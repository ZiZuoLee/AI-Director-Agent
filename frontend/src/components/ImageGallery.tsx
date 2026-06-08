import type { GeneratedImage } from "../types";

interface ImageGalleryProps {
  images: GeneratedImage[];
  title?: string;
}

export default function ImageGallery({ images, title = "生成图像" }: ImageGalleryProps) {
  if (!images.length) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-cinema-900/70 p-5">
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {images.map((image) => (
          <figure
            key={`${image.shot_id}-${image.image_path}`}
            className="overflow-hidden rounded-xl border border-white/10 bg-cinema-950"
          >
            {image.image_url ? (
              <img
                src={image.image_url}
                alt={`镜头 ${image.shot_id}`}
                className="aspect-video w-full object-cover"
              />
            ) : (
              <div className="flex aspect-video items-center justify-center text-sm text-gray-500">
                图像加载中
              </div>
            )}
            <figcaption className="space-y-1 p-3 text-xs text-gray-400">
              <p className="font-medium text-cinema-accent">镜头 {image.shot_id}</p>
              <p className="line-clamp-3 text-gray-500">{image.prompt}</p>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}
