using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
namespace MyConsoleApp
{
    public class ESearch
    {
        private static readonly HttpClient client = new HttpClient();

        public async Task<string[]> Search(string tableName, string inputStr)
        {
            var requestData = new
            {
                table_name = tableName,  // 确保字段名称与 Python 代码一致
                input_str = inputStr
            };

            string jsonData = JsonConvert.SerializeObject(requestData);
            var content = new StringContent(jsonData, Encoding.UTF8, "application/json");

            try
            {
                var response = await client.PostAsync("http://127.0.0.1:5000/search", content);
                response.EnsureSuccessStatusCode();

                var responseBody = await response.Content.ReadAsStringAsync();

                var jsonResponse = JArray.Parse(responseBody);

                string[] result = new string[150];


                //if (jsonResponse.ValueKind == JsonValueKind.Array)
                {
                    int count = 0;
                    foreach (var item in jsonResponse)
                    {
                        if (count >= 3) break;
                        //Console.WriteLine(item);
                        result[count] = UnescapeUnicode(item.ToString());
                        //Console.WriteLine(result[count]);
                        count++;
                    }
                }

                return result;
            }
            catch (HttpRequestException e)
            {
                // 处理请求异常
                Console.WriteLine($"Request error: {e.Message}");
                return null;
            }
        }

        public static string UnescapeUnicode(string str)  // 将unicode转义序列(\uxxxx)解码为字符串
        {
            return (System.Text.RegularExpressions.Regex.Unescape(str));
        }

    }
}