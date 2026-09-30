SELECT GET_PRESIGNED_URL(@SUPPLY_CHAIN_COPILOT.APP.PPT_OUTPUT, 'Supply_Chain_Copilot_Hackathon.pptx', 3600) AS download_url;

SELECT GET_PRESIGNED_URL(@SUPPLY_CHAIN_COPILOT.APP.PPT_OUTPUT, 'Supply_Chain_Copilot_Hackathon.pptx', 3600);

GET @SUPPLY_CHAIN_COPILOT.APP.PPT_OUTPUT/Supply_Chain_Copilot_Hackathon.pptx file:///your/local/path/;


https://sun6cgsfcb1stg.blob.core.windows.net/stageszz04f957be-1354-49c6-8986-8a2abb31b93b/Supply_Chain_Copilot_Hackathon.pptx?sv=2026-02-06&se=2026-09-28T05%3A58%3A31Z&skoid=0daabbde-c0bb-4bfa-aec1-3a01d67f5400&sktid=e4d47aa2-dcac-479c-86bd-3e359a37bf12&skt=2026-09-28T04%3A58%3A31Z&ske=2026-10-05T04%3A57%3A31Z&sks=b&skv=2026-02-06&sr=b&sp=r&sig=%2FJJjx275kAVzIwH3qrmOomv7I0VKFOgfPFcOV23eCkg%3D