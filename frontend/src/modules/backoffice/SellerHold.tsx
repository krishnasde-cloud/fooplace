type SellerHoldProps = {
  title: string;
  message: string;
};

export function SellerHold({ title, message }: SellerHoldProps) {
  return (
    <section className="listings-page">
      <h1>{title}</h1>
      <p className="listings-empty">{message}</p>
    </section>
  );
}
