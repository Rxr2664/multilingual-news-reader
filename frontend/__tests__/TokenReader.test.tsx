import { render, screen, fireEvent } from "@testing-library/react";
import TokenReader, { difficultyBand } from "@/components/TokenReader";
import { TokenSpan } from "@/lib/api";

const tokens: TokenSpan[] = [
  { text: "Malgré", lemma: "malgré", is_entity: false, is_punct: false, unknown: true },
  { text: " ", lemma: " ", is_entity: false, is_punct: true, unknown: false },
  { text: "Paris", lemma: "Paris", is_entity: true, is_punct: false, unknown: false },
];

test("unknown tokens are highlighted", () => {
  render(
    <TokenReader tokens={tokens} onKnow={() => {}} onUnknown={() => {}} selected={null} onSelect={() => {}} />
  );
  const word = screen.getByText("Malgré");
  expect(word.className).toContain("unknown");
});

test("clicking a word selects it", () => {
  const onSelect = jest.fn();
  render(
    <TokenReader tokens={tokens} onKnow={() => {}} onUnknown={() => {}} selected={null} onSelect={onSelect} />
  );
  fireEvent.click(screen.getByText("Malgré"));
  expect(onSelect).toHaveBeenCalledWith("malgré");
});

test("difficulty bands", () => {
  expect(difficultyBand(6)).toBe("comfort");
  expect(difficultyBand(15)).toBe("stretch");
  expect(difficultyBand(40)).toBe("hard");
});
