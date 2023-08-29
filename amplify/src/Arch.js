import { Image } from '@aws-amplify/ui-react';

function ArchView() {

    return(
        <Image
            alt="This App Arch Diagram"
            src="/GenAIAppArch.png"
            objectFit="initial"
            objectPosition="50% 50%"
            backgroundColor="initial"
            height="75%"
            width="75%"
            opacity="100%" />

    ) ;
}

export default ArchView ;