# Hack a LLM - Level I 

This is a simple exercise to practice basic LLM hacking technics.

## To run the code 

### Directly from source

```bash
git clone https://github.com/JedhaBootcamp/hack-a-llm-level-1
cd ./hack-a-llm-level-1
docker build . -t jedha/hack-a-llm-level-1
docker run -d \
    --name hack-a-llm-level-1 \
    -p 80:80
    --restart=always \
    jedha/hack-a-llm-level-1
```

### From docker hub

```bash
docker run -d \
    --name hack-a-llm-level-1 \
    -p 80:80
    --restart=always \
    jedha/hack-a-llm-level-1
```

## Don't forget

* Make sure `OPENAI_API_KEY` is set for the code to run. 
