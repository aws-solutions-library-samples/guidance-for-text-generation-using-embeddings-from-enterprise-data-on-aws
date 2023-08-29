import React, { useState } from 'react'
import { API, Auth } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { TextAreaField, Flex, ThemeProvider, Button } from '@aws-amplify/ui-react';
import { CircularProgress } from '@mui/material';

import cnf from './cdk-exports.json';

function GenerateText() {
    const [gentdTxt, setGentdTxt] = useState([]) ;
    const [promptTxt, setPromptTxt] = useState([]);
    const [loading, setLoading] = useState(false);
    const [show, setShow] = useState(false) ;    

    async function CallModelAPI() {
        setLoading(true);
        setGentdTxt("In Progress.....");
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
    
        API.post(cnf.GenAIAmplifyAppAPILambdaStack.txt2txtapiname, "/" + cnf.GenAIAmplifyAppAPILambdaStack.txt2txtapiname, reqPayload).then((response) => {
            setGentdTxt(response['generated_texts']) ;
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
                        <TextAreaField autoComplete="off" direction="column" hasError={false} isDisabled={false} isReadOnly={false} isRequired={true}
                            label="Prompt Input here:"
                            labelHidden={false} 
                            name="prompt_input"
                            placeholder="Translate to German:  My name is Arthur"
                            rows="8"
                            size="small"
                            wrap="nowrap"
                            onChange={(e) => setPromptTxt(e.currentTarget.value)}>
                        </TextAreaField>

                        <Button loadingText="loading..." onClick={() => CallModelAPI()} ariaLabel=""> Generate!!!</Button>
                        
                        { !loading && show && (
                            <TextAreaField autoComplete="off" descriptiveText="Model Generated Text here:" direction="column" hasError={false} isDisabled={false} isReadOnly={true} isRequired={false}
                                label="Generated Output"
                                labelHidden={false} 
                                name="generated_output"
                                placeholder={ gentdTxt }
                                rows="8"
                                size="large">
                            </TextAreaField>
                        ) }
                        
                        <div> 
                            { loading && ( <CircularProgress size={96} color="secondary"/> )}
                        </div> 
                                                
                    </Flex>
                </ThemeProvider>
            )}
        </Authenticator>
    );
    
} 

export default GenerateText ;
