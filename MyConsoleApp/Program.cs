using System;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace MyConsoleApp
{
    public class Program
    {
        public static async Task Main(string[] args)
        {
            // 设置控制台输出编码为UTF-8
            Console.OutputEncoding = Encoding.UTF8;

            ESearch eSearch = new ESearch();
            //string[] results = await eSearch.Search("command", "赌博");
            var task = Task.Run(async () =>
            {
                return await eSearch.Search("command", "赌博");
            });
            string[] results = task.GetAwaiter().GetResult();

        }
    }
}