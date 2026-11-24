const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" });

export function formatCoursePrice(price: number): string {
  return price === 0 ? "Free" : inr.format(price);
}
