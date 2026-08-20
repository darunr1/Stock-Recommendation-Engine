import InviteLanding from "@/components/InviteLanding";
export default async function Invite({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  return <InviteLanding code={code} />;
}
