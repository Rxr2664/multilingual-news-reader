import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ArticlePage from "@/app/article/[id]/page";
import { ArticleDetail, api } from "@/lib/api";

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "1" }),
}));

jest.mock("@/components/Shell", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => children,
}));

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  api: jest.fn(),
}));

const mockedApi = api as jest.Mock;

const article: ArticleDetail = {
  id: 1,
  title: "Malgré la pluie",
  url: "https://example.com/a1",
  source_name: "Le Monde",
  country: "FR",
  language: "fr",
  published_at: "2026-09-23T08:00:00Z",
  body: "Malgré la pluie",
  unknown_pct: 50,
  tokens: [
    { text: "Malgré", lemma: "malgré", is_entity: false, is_punct: false, unknown: true },
    { text: " ", lemma: " ", is_entity: false, is_punct: true, unknown: false },
    { text: "la", lemma: "le", is_entity: false, is_punct: false, unknown: false },
    { text: " ", lemma: " ", is_entity: false, is_punct: true, unknown: false },
    { text: "pluie", lemma: "pluie", is_entity: false, is_punct: false, unknown: true },
  ],
};

beforeEach(() => {
  mockedApi.mockReset();
});

async function markKnown(word: string) {
  fireEvent.click(await screen.findByText(word));
  fireEvent.click(screen.getByText("I know this"));
}

test("a word stays known when saving succeeds", async () => {
  mockedApi.mockImplementation(async (path: string) => (path === "/articles/1" ? article : {}));
  render(<ArticlePage />);

  await markKnown("Malgré");

  await waitFor(() =>
    expect(mockedApi).toHaveBeenCalledWith(
      "/vocab/know",
      expect.objectContaining({ method: "POST" })
    )
  );
  expect(screen.getByText("Malgré").className).not.toContain("unknown");
  expect(screen.queryByText(/Couldn't save/)).toBeNull();
});

test("the unknown percentage is refreshed after a save", async () => {
  let loads = 0;
  mockedApi.mockImplementation(async (path: string) => {
    if (path === "/articles/1") return loads++ === 0 ? article : { ...article, unknown_pct: 25 };
    return {};
  });
  render(<ArticlePage />);
  expect(await screen.findByText(/· 50% unknown/)).toBeInTheDocument();

  await markKnown("Malgré");

  expect(await screen.findByText(/· 25% unknown/)).toBeInTheDocument();
});

test("a word is rolled back when saving fails", async () => {
  mockedApi.mockImplementation(async (path: string) => {
    if (path === "/articles/1") return article;
    throw new Error("network down");
  });
  render(<ArticlePage />);

  await markKnown("Malgré");

  expect(await screen.findByText(/Couldn't save "malgré"/)).toBeInTheDocument();
  expect(screen.getByText("Malgré").className).toContain("unknown");
  expect(screen.getByText("pluie").className).toContain("unknown");
  // Initial load and the failed save only; no refresh after a failure.
  expect(mockedApi).toHaveBeenCalledTimes(2);
});
