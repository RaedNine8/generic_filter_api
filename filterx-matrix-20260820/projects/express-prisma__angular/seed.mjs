import { PrismaClient } from '@prisma/client';
const db = new PrismaClient();
await db.book.deleteMany(); await db.author.deleteMany();
await db.author.create({data:{name:'Ada',books:{create:[{title:'Alpha Filtering',genre:'Tech',price:'10.00',note:'first'}]}}});
await db.author.create({data:{name:'Bob',books:{create:[{title:'Beta Search',genre:'Tech',price:'30.00'},{title:'Gamma Grouping',genre:'Business',price:'40.00',note:'last'}]}}});
await db.$disconnect();
