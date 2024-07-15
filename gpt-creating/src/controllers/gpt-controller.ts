import {Request, Response} from 'express';
import GptService from "../services/gpt-services";

export default class GptController {
    private gptService: GptService

    constructor(gptService:GptService){
        this.gptService = gptService
    }

    getCode = async (req: Request, res: Response) => {
        console.log('Received request to generate Manim code.');
        const { gptService } = req.body;
        if(!gptService){
            return res.status(400).json({error:'Prompt is required'})
        }
        try{
            const response = await this.gptService.generateManimCode(gptService);
            res.status(200).json(response);
        } catch(error:any) {
            res.status(500).json({error:error.message})
        }
    }
}