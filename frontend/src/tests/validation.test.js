import { describe, expect, it } from "vitest";
import { isValidEmail, validateImageFile, validateImageFiles } from "../utils/validation";

describe("frontend validation", () => {
  it("accepts a valid email and rejects malformed input", () => {
    expect(isValidEmail("student@example.com")).toBe(true);
    expect(isValidEmail("student-at-example")).toBe(false);
  });

  it("rejects unsupported image content types", () => {
    const file = new File(["content"], "face.gif", { type: "image/gif" });
    expect(validateImageFile(file)).toMatch(/JPG, JPEG, and PNG/i);
  });

  it("rejects multiple image selections", () => {
    const one = new File(["a"], "one.jpg", { type: "image/jpeg" });
    const two = new File(["b"], "two.png", { type: "image/png" });
    expect(validateImageFiles([one, two])).toMatch(/one/i);
  });
});
