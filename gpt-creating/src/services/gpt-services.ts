import { Queue } from "bullmq";
import ICode from "../interfaces/code.interface";
import Code from "../models/code.model";
import { openai } from "../openai";
//import amqp from 'amqplib';

const REDIS_HOST = process.env.REDIS_HOST || 'localhost';
const REDIS_PORT = process.env.REDIS_PORT ? parseInt(process.env.REDIS_PORT) : 6379;

export default class GptService {
    private systemPrompt: string;
    private queue: Queue;

    //private rabbitmqUrl: string;
    //private queueName: string;
    

    constructor() {
        this.systemPrompt = `
        You are a professional teacher who explains math through visualization using Manim. 
        You should create Manim code from the user prompt.
        Please, return your response in the following JSON array format: 
        {
            "manim_code": [
                {
                    "code": "manim code"
                }
            ]
        }
        If the user prompt is irrelevant, return an empty array of code.
        `;
        
        this.queue = new Queue('manim-queue', {
            connection: {
                host: REDIS_HOST,
                port: REDIS_PORT
            }
        });
    }

    async generateManimCode(userPrompt: string) {
        try{
            const response = await openai.chat.completions.create({
                model: 'gpt-4o',
                messages: [
                    {
                        role: 'system',
                        content: this.systemPrompt,
                    },
                    {
                        role: 'user',
                        content: userPrompt,
                    },
                ],
            });

            const resJson: string | null = response.choices[0].message.content;
            if(resJson) {
                const parsedRes = JSON.parse(resJson);
                const code = parsedRes.manim_code as ICode[];

                if(code.length > 0) {
                    console.log(code);
                    Code.insertMany(code[0]);
                }
                return code;
            } else {
                return [];                
            }
        } catch(e:any) {
            console.log(e.message);
            return [];
        }
    }

    private async publishToQueue(code: ICode) {
        try {
            await this.queue.add('manim-job', code);
            console.log("Job added to the queue", code);
        } catch (error) {
            console.error('Error adding job to the queue:', error);
            throw error;
        }
    }

    /*
    private async sendToRabbitMQ(code: ICode) {
        try {
            const connection = await amqp.connect(this.rabbitmqUrl);
            const channel = await connection.createChannel();

            await channel.assertQueue(this.queueName, { durable: true });

            const message = JSON.stringify(code);
            channel.sendToQueue(this.queueName, Buffer.from(message), { persistent: true });

            console.log(" [x] Sent %s", message);

            await channel.close();
            await connection.close();
        } catch (error) {
            console.error('Error sending message to RabbitMQ:', error);
            throw error;
        }
    }
    */
}