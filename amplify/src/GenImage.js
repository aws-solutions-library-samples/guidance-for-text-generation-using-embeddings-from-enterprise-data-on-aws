import React, { useState } from 'react'
import { API, Auth } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { TextAreaField, Flex, ThemeProvider, Button, Image } from '@aws-amplify/ui-react';
import { CircularProgress } from '@mui/material';

import cnf from './cdk-exports.json';

function GenerateImage() {
    const [gentdImg, setGentdImg] = useState(String) ;
    const [promptTxt, setPromptTxt] = useState([]);
    const [loading, setLoading] = useState(false);
    const [show, setShow] = useState(false) ;

    async function CallModelAPI() {
        setLoading(true);
        setGentdImg("");
        console.log("promptTxt: " + promptTxt) ;
        const reqPayload = {
            body: {
                "data": promptTxt
            },
            headers: {
                Authorization: `Bearer ${(await Auth.currentSession())
                  .getIdToken()
                  .getJwtToken()}`
            }             
        } ;
    
        API.post(cnf.GenAIAmplifyAppAPILambdaStack.txt2imgapiname, "/" + cnf.GenAIAmplifyAppAPILambdaStack.txt2imgapiname, reqPayload).then((response) => {
            var base64Flag = 'data:image/png;base64,';
            var img = base64Flag + response['generated_images'][0] ;
            setGentdImg(img);
            setLoading(false);
            setShow(true);
        }).catch((error) => {
            console.log(error.response);
            setLoading(false);
            setShow(true);
        });
    }

    return(
        <Authenticator hideSignUp={true}>
            {({ signOut, user }) => (
                <ThemeProvider>
                    <Flex direction="column" gap="1.5rem">
                        <TextAreaField
                            placeholder="cottage in impressionist style"
                            label="Enter a description of image to generate -"
                            onChange={(e) => setPromptTxt(e.currentTarget.value)}
                        />

                        <Button loadingText="loading..." onClick={() => CallModelAPI()} ariaLabel=""> Generate!!!</Button>
                        
                        <div> 
                            { loading && ( <CircularProgress size={96} color="secondary"/> )}
                        </div> 
                        { !loading && show && ( <Image src= { gentdImg } width={"1536px"} height={"1536px"}  alt={ "" }/>) }
                                                
                    </Flex>
                </ThemeProvider>
            )}
        </Authenticator>
    );
    
} 

export default GenerateImage ;