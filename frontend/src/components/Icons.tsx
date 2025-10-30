import type { SVGProps } from "react";

function SvgIcon(props: SVGProps<SVGSVGElement>) {
  return <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" {...props} />;
}

export function SettingsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.8} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37a1.724 1.724 0 0 0 2.572-1.065z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" />
    </SvgIcon>
  );
}

export function AnalysisIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.8} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5.586a1 1 0 0 1 .707.293l5.414 5.414a1 1 0 0 1 .293.707V19a2 2 0 0 1-2 2z" />
    </SvgIcon>
  );
}

export function SendIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.8} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
    </SvgIcon>
  );
}

export function MicIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.6} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19 11a7 7 0 0 1-7 7 7 7 0 0 1-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 0 1-3-3V5a3 3 0 1 1 6 0v6a3 3 0 0 1-3 3z"
      />
    </SvgIcon>
  );
}

export function MicOffIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.6} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15.586 15.586a7 7 0 0 1-9.172-9.172m9.172 9.172a7 7 0 0 0-9.172-9.172m9.172 9.172L5.414 5.414M19 11a7 7 0 0 1-1.42 4.14M5 11a7 7 0 0 0 1.42 4.14M12 19v2m0 0H9m3 0h3"
      />
    </SvgIcon>
  );
}

export function UserIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.8} {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z" />
    </SvgIcon>
  );
}

export function BotIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.8} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m14 0h2M3 15h2m14 0h2M9 21h6a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2z"
      />
    </SvgIcon>
  );
}

export function TrashIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.8} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19 7l-.867 12.142A2 2 0 0 1 16.138 21H7.862a2 2 0 0 1-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v3M4 7h16"
      />
    </SvgIcon>
  );
}

export function EditIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.8} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M11 5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-5m-1.414-9.414a2 2 0 1 1 2.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
      />
    </SvgIcon>
  );
}

export function CopyIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <SvgIcon viewBox="0 0 24 24" strokeWidth={1.8} {...props}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M8 16H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2m-6 12h8a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-8a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2z"
      />
    </SvgIcon>
  );
}



