# GIF animation generator
Demontate the creation of a GIF animation generator that leverages the power of the large language model(LLMs) and image generation AI.

By combining LangGraph for workfow management ```gpt-4.o-mini``` for text generator and ```gpt-image-2.5-flare ``` for image creation.



This project aims to show how various AI technologies can intergated to create seamless workflow that transform single prompt into a dynamic visual story.


## Methob:

The GIF generation process follows these hight-level step:
1. Character/Scene Description: Base on the user's input query, The system generates a detailed description of the main character or scene.
2. Plot Generation: Using the character discription and initial query, a 5 step plot is created, 
3. Image prompt creation: For each step of the plot, a specific image promprs is generated, ensure consistancy across the frames.
4. Image generation: Create image based on user prompt.
5. GIF assembly: The generation image are compile into a GIF animation


