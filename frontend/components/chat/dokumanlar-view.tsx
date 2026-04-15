"use client";

const posts = [
  {
    id: 1,
    title: "Boost your conversion rate",
    href: "#",
    description:
      "Illo sint voluptas. Error voluptates culpa eligendi. Hic vel totam vitae illo. Non aliquid explicabo necessitatibus unde. Sed exercitationem placeat consectetur nulla deserunt vel. Iusto corrupti dicta.",
    imageUrl:
      "https://images.unsplash.com/photo-1496128858413-b36217c2ce36?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3603&q=80",
  },
  {
    id: 2,
    title: "How to use search engine optimization to drive sales",
    href: "#",
    description:
      "Optio cum necessitatibus dolor voluptatum provident commodi et. Qui aperiam fugiat nemo cumque.",
    imageUrl:
      "https://images.unsplash.com/photo-1547586696-ea22b4d4235d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
  },
  {
    id: 3,
    title: "Improve your customer experience",
    href: "#",
    description:
      "Cupiditate maiores ullam eveniet adipisci in doloribus nulla minus. Voluptas iusto libero adipisci rem et corporis.",
    imageUrl:
      "https://images.unsplash.com/photo-1492724441997-5dc865305da7?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
  },
  {
    id: 4,
    title: "Scale your team with confidence",
    href: "#",
    description:
      "Natus aut nobis officiis perferendis. Aspernatur iste consequatur quas et nulla.",
    imageUrl:
      "https://images.unsplash.com/photo-1519389950473-47ba0277781c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
  },
  {
    id: 5,
    title: "Build trust with your audience",
    href: "#",
    description:
      "Maiores et perferendis eaque quod labore quia quia. Sit quos amet ullam beatae ex.",
    imageUrl:
      "https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
  },
  {
    id: 6,
    title: "The art of launching a product",
    href: "#",
    description:
      "Quisquam amet totam et quia blanditiis. Veritatis ratione cumque similique et.",
    imageUrl:
      "https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
  },
  {
    id: 7,
    title: "Why design systems matter",
    href: "#",
    description:
      "Sed quia magni omnis voluptatum eum dolores quidem. Totam ratione voluptas dolorem expedita temporibus.",
    imageUrl:
      "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
  },
  {
    id: 8,
    title: "Modern engineering culture",
    href: "#",
    description:
      "Laboriosam voluptates et rerum odit illum tempore. Et soluta fugit iusto omnis a consequatur voluptatem.",
    imageUrl:
      "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
  },
  {
    id: 9,
    title: "From idea to MVP in 30 days",
    href: "#",
    description:
      "Voluptatem aperiam ut iste odit sunt quas maiores. Dolores unde sapiente repudiandae aut iste maxime.",
    imageUrl:
      "https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
  },
];

export function DokumanlarView() {
  return (
    <div className="relative z-1 flex-1 overflow-y-auto pt-8 pb-16 sm:pt-10 sm:pb-20">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto flex max-w-2xl flex-col items-center">
          <h2 className="text-center font-semibold text-2xl tracking-tight text-foreground md:text-3xl">
            Dokümanlar
          </h2>
          <p className="mt-3 text-center text-muted-foreground/80 text-sm">
            TÜBİTAK dokümanları, yayınları ve kaynakları.
          </p>
        </div>
        <div className="mx-auto mt-12 grid max-w-2xl auto-rows-fr grid-cols-1 gap-8 lg:mx-0 lg:max-w-none lg:grid-cols-3">
          {posts.map((post) => (
            <article
              key={post.id}
              className="relative isolate flex flex-col justify-end overflow-hidden rounded-2xl bg-muted px-8 pt-48 pb-6 sm:pt-32 lg:pt-48"
            >
              <img
                alt=""
                src={post.imageUrl}
                className="absolute inset-0 -z-10 size-full object-cover"
              />
              <div className="absolute inset-0 -z-10 bg-linear-to-t from-black/80 via-black/40" />
              <div className="absolute inset-0 -z-10 rounded-2xl inset-ring inset-ring-white/10" />

              <h3 className="text-lg/6 font-semibold text-white">
                <a href={post.href}>
                  <span className="absolute inset-0" />
                  {post.title}
                </a>
              </h3>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
