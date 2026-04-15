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
    date: "Mar 16, 2020",
    datetime: "2020-03-16",
  },
  {
    id: 2,
    title: "How to use search engine optimization to drive sales",
    href: "#",
    description:
      "Optio cum necessitatibus dolor voluptatum provident commodi et. Qui aperiam fugiat nemo cumque.",
    imageUrl:
      "https://images.unsplash.com/photo-1547586696-ea22b4d4235d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
    date: "Mar 10, 2020",
    datetime: "2020-03-10",
  },
  {
    id: 3,
    title: "Improve your customer experience",
    href: "#",
    description:
      "Cupiditate maiores ullam eveniet adipisci in doloribus nulla minus. Voluptas iusto libero adipisci rem et corporis. Nostrud sint anim sunt aliqua. Nulla eu labore irure incididunt velit cillum quis magna dolore.",
    imageUrl:
      "https://images.unsplash.com/photo-1492724441997-5dc865305da7?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
    date: "Feb 12, 2020",
    datetime: "2020-02-12",
  },
  {
    id: 4,
    title: "Scale your team with confidence",
    href: "#",
    description:
      "Natus aut nobis officiis perferendis. Aspernatur iste consequatur quas et nulla. Expedita voluptate aut dolor ab voluptatem ut quos.",
    imageUrl:
      "https://images.unsplash.com/photo-1519389950473-47ba0277781c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
    date: "Feb 02, 2020",
    datetime: "2020-02-02",
  },
  {
    id: 5,
    title: "Build trust with your audience",
    href: "#",
    description:
      "Maiores et perferendis eaque quod labore quia quia. Sit quos amet ullam beatae ex. Accusantium non sint ut distinctio.",
    imageUrl:
      "https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
    date: "Jan 28, 2020",
    datetime: "2020-01-28",
  },
  {
    id: 6,
    title: "The art of launching a product",
    href: "#",
    description:
      "Quisquam amet totam et quia blanditiis. Veritatis ratione cumque similique et. Tempora quia autem atque voluptas.",
    imageUrl:
      "https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
    date: "Jan 12, 2020",
    datetime: "2020-01-12",
  },
  {
    id: 7,
    title: "Why design systems matter",
    href: "#",
    description:
      "Sed quia magni omnis voluptatum eum dolores quidem. Totam ratione voluptas dolorem expedita temporibus laboriosam impedit ullam.",
    imageUrl:
      "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
    date: "Dec 20, 2019",
    datetime: "2019-12-20",
  },
  {
    id: 8,
    title: "Modern engineering culture",
    href: "#",
    description:
      "Laboriosam voluptates et rerum odit illum tempore. Et soluta fugit iusto omnis a consequatur voluptatem est et.",
    imageUrl:
      "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
    date: "Dec 05, 2019",
    datetime: "2019-12-05",
  },
  {
    id: 9,
    title: "From idea to MVP in 30 days",
    href: "#",
    description:
      "Voluptatem aperiam ut iste odit sunt quas maiores. Dolores unde sapiente repudiandae aut iste maxime non doloremque.",
    imageUrl:
      "https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=3270&q=80",
    date: "Nov 18, 2019",
    datetime: "2019-11-18",
  },
];

export function HaberlerDuyurularView() {
  return (
    <div className="relative z-1 flex-1 overflow-y-auto pt-8 pb-16 sm:pt-10 sm:pb-20">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto flex max-w-2xl flex-col items-center">
          <h2 className="text-center font-semibold text-2xl tracking-tight text-foreground md:text-3xl">
            Haberler ve Duyurular
          </h2>
          <p className="mt-3 text-center text-muted-foreground/80 text-sm">
            TÜBİTAK gündeminden seçilmiş son haberler ve duyurular.
          </p>
        </div>
        <div className="mx-auto mt-12 grid max-w-2xl grid-cols-1 gap-x-8 gap-y-16 lg:mx-0 lg:max-w-none lg:grid-cols-3">
          {posts.map((post) => (
            <article
              key={post.id}
              className="flex flex-col items-start justify-between"
            >
              <div className="relative w-full">
                <img
                  alt=""
                  src={post.imageUrl}
                  className="aspect-video w-full rounded-2xl bg-muted object-cover sm:aspect-2/1 lg:aspect-3/2"
                />
                <div className="absolute inset-0 rounded-2xl inset-ring inset-ring-white/10" />
              </div>
              <div className="flex max-w-xl grow flex-col justify-between">
                <div className="mt-8 flex items-center gap-x-4 text-xs">
                  <time
                    dateTime={post.datetime}
                    className="text-muted-foreground"
                  >
                    {post.date}
                  </time>
                </div>
                <div className="group relative grow">
                  <h3 className="mt-3 text-lg/6 font-semibold text-foreground group-hover:text-muted-foreground">
                    <a href={post.href}>
                      <span className="absolute inset-0" />
                      {post.title}
                    </a>
                  </h3>
                  <p className="mt-5 line-clamp-3 text-sm/6 text-muted-foreground">
                    {post.description}
                  </p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
