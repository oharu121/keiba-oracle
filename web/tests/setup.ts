import { vi } from "vitest";

// Mock framer-motion to avoid animation issues in tests
vi.mock("framer-motion", () => ({
  motion: {
    div: "div",
    span: "span",
    circle: "circle",
    path: "path",
    svg: "svg",
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
  useAnimation: () => ({
    start: vi.fn(),
    stop: vi.fn(),
  }),
  useMotionValue: (initial: number) => ({
    get: () => initial,
    set: vi.fn(),
  }),
  useTransform: (value: unknown, input: number[], output: number[]) => ({
    get: () => output[0],
  }),
}));
