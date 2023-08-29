import React, { useState } from 'react'
import { API, Auth } from 'aws-amplify';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { TextAreaField, Flex, ThemeProvider, Button, View, Heading } from '@aws-amplify/ui-react';
import { CircularProgress } from '@mui/material';

import cnf from './cdk-exports.json';

function LegalLLMRAG() {
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
    
        API.post(cnf.GenAIAmplifyAppAPILambdaStack.llmragapiname, "/" + cnf.GenAIAmplifyAppAPILambdaStack.llmragapiname, reqPayload).then((response) => {
            setGentdTxt(response) ;
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
                            label="Legal Question Input here:"
                            labelHidden={false} 
                            name="prompt_input"
                            placeholder="What is the definition of crime of battery?"
                            rows="8"
                            size="small"
                            wrap="nowrap"
                            onChange={(e) => setPromptTxt(e.currentTarget.value)}>
                        </TextAreaField>
                        <Button loadingText="loading..." onClick={() => CallModelAPI()} ariaLabel=""> Answer!!!</Button>

                        { !loading && show && 

                            <div>
                                <Heading level={5}>
                                    Document Name: { gentdTxt.doc_id }
                                </Heading>
                                <Heading level={5}>
                                    Passage:
                                </Heading>
                                <View>
                                    { gentdTxt.passage }
                                </View>
                                <Heading level={5}>
                                    Answer:
                                </Heading>                                
                                { gentdTxt.ans.generated_texts.map(d => (
                                    <View>{d}</View>
                                )) }
                            </div>                
                        } 

                        <div> 
                            { loading && ( <CircularProgress size={96} color="secondary"/> )}
                        </div> 
                        </Flex>
                </ThemeProvider>
            )}
        </Authenticator>
    );                                                    
}

export default LegalLLMRAG;