using System;
using MySql.Data.MySqlClient;

class Program
{
    static void Main()
    {
        // 连接字符串
        string strConn = "server=127.0.0.1;port=3306;database=gmcommand;user=root;password=123456;Charset=utf8";
        
        // 创建连接对象
        using (MySqlConnection conn = new MySqlConnection(strConn))
        {
            try
            {
                // 打开连接
                conn.Open();
                Console.WriteLine("Connection successful!");

                // 创建 SQL 查询
                string sql = "SELECT * FROM command Limit 10";

                // 创建命令对象
                MySqlCommand cmd = new MySqlCommand(sql, conn);

                // 执行查询并读取结果
                using (MySqlDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        // 读取每一行数据
                        Console.WriteLine($"Column1: {reader["name"]}, Column2: {reader["body"]}");
                    }
                }
            }
            catch (MySqlException ex)
            {
                // 捕获并打印异常信息
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
    }
}