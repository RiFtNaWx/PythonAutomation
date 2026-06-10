import os
import time
import serial
import pyvisa
import pandas as pd
import win32com.client as win32
from typing import List, Tuple, Optional

# 设备连接地址
url_DP832_0 = "USB0::0x1AB1::0x0E11::DP8C274303823::INSTR"
url_DG832_0 = "USB0::0x1AB1::0x0646::DG8Q274702441::INSTR"
url_MSO5000 = "USB0::0x1AB1::0x0515::MS5A274703490::INSTR"

# 文件路径配置
BASE_DIR = os.path.abspath(".")
BACKUP_DIR = os.path.abspath("backup_data")
os.makedirs(BACKUP_DIR, exist_ok=True)

# 全局资源管理器
rm = pyvisa.ResourceManager()


def get_next_file_number(base_name: str, extension: str = "xlsx") -> Tuple[str, int]:
    """获取下一个可用的文件编号"""
    index = 1
    while True:
        filename = f"{base_name}_{index}.{extension}"
        if not os.path.exists(os.path.join(BASE_DIR, filename)):
            return filename, index
        index += 1


def kill_excel_process():
    """强制结束所有Excel进程"""
    try:
        os.system('taskkill /f /im excel.exe')
        time.sleep(1)
    except:
        pass


def save_to_excel(results_gbw: List[list], results_sr: List[list]) -> bool:
    """保存数据到Excel（三重保护机制）"""

    # 获取下一个可用的文件编号
    excel_filename, file_num = get_next_file_number("test_results")
    EXCEL_PATH = os.path.abspath(excel_filename)

    def save_with_pandas():
        """方法1：使用pandas保存"""
        with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl') as writer:
            pd.DataFrame(results_gbw, columns=["温度(°C)", "电压(V)", "GBW(MHz)"]).to_excel(
                writer, sheet_name='GBW', index=False)
            pd.DataFrame(results_sr, columns=["温度(°C)", "电压(V)", "正SR(V/μs)", "负SR(V/μs)"]).to_excel(
                writer, sheet_name='SR', index=False)

    def save_with_win32com():
        """方法2：使用win32com保存"""
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        excel.Visible = False
        try:
            wb = excel.Workbooks.Add()

            # 保存GBW数据
            sheet = wb.Sheets.Add(After=wb.Sheets(wb.Sheets.Count))
            sheet.Name = "GBW"
            sheet.Range("A1:D1").Value = ["温度(°C)", "电压(V)", "GBW(MHz)", "测试时间"]
            for i, row in enumerate(results_gbw, start=2):
                sheet.Range(f"A{i}:D{i}").Value = row + [time.strftime("%Y-%m-%d %H:%M:%S")]

            # 保存SR数据
            sheet = wb.Sheets.Add(After=wb.Sheets(wb.Sheets.Count))
            sheet.Name = "SR"
            sheet.Range("A1:E1").Value = ["温度(°C)", "电压(V)", "正SR(V/μs)", "负SR(V/μs)", "测试时间"]
            for i, row in enumerate(results_sr, start=2):
                sheet.Range(f"A{i}:E{i}").Value = row + [time.strftime("%Y-%m-%d %H:%M:%S")]

            wb.SaveAs(EXCEL_PATH)
            return True
        finally:
            wb.Close()
            excel.Quit()

    def save_backup_csv():
        """方法3：保存CSV备份"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        pd.DataFrame(results_gbw).to_csv(os.path.join(BACKUP_DIR, f"gbw_backup_{timestamp}.csv"), index=False)
        pd.DataFrame(results_sr).to_csv(os.path.join(BACKUP_DIR, f"sr_backup_{timestamp}.csv"), index=False)

    try:
        kill_excel_process()
        save_with_pandas()
        print(f"数据成功保存到 {EXCEL_PATH} (文件编号: {file_num})")
        return True
    except Exception as e:
        print(f"pandas保存失败: {e}")
        try:
            kill_excel_process()
            save_with_win32com()
            print(f"通过win32com保存成功 (文件编号: {file_num})")
            return True
        except Exception as e:
            print(f"win32com保存失败: {e}")
            try:
                save_backup_csv()
                print("数据已备份为CSV文件")
                return False
            except Exception as e:
                print(f"备份保存失败: {e}")
                return False


def measure_gbw(power_supply, signal_generator, oscilloscope, vcc: float, amp: float, gain: int) -> Optional[float]:
    """测量增益带宽积"""
    try:
        # 电源设置
        power_supply.write(f":SOUR1:VOLT {vcc / 2};:CURR 0.1")
        power_supply.write(f":SOUR2:VOLT {vcc / 2};:CURR 0.1")
        power_supply.write(":OUTP CH1,ON;:OUTP CH2,ON;:OUTP CH3,OFF")
        time.sleep(1)

        # 信号发生器设置
        signal_generator.write(f":SOUR1:APPL:SIN 1000,{amp * 0.001},0,0")
        signal_generator.write(":OUTP1 ON")
        time.sleep(1)

        # 示波器设置
        oscilloscope.write(":AUToscale")
        time.sleep(3)

        # 初始幅度测量
        initial_amps = []
        for _ in range(5):
            try:
                amp_value = float(oscilloscope.query(":MEAS:ITEM? VAMP,CHAN2"))
                if amp_value < 1e10:  # 过滤无效值
                    initial_amps.append(amp_value)
            except:
                continue
            time.sleep(0.1)

        if not initial_amps:
            raise ValueError("无法获取有效初始幅度")

        target_amp = (sum(initial_amps) / len(initial_amps)) * 0.707
        print(f"targe:{target_amp}")

        # 二分法查找GBW
        low, high = 500, 150000
        while high - low > 100:
            mid = (low + high) / 2
            #signal_generator.write(f":SOUR1:APPL:SIN {mid},{amp * 0.001},0,0")
            signal_generator.write(f":SOUR1:FREQ {mid}")
            time.sleep(0.5)

            # 测量当前幅度
            current_amps = []
            for _ in range(3):
                try:
                    amp_value = float(oscilloscope.query(":MEAS:ITEM? VAMP,CHAN2"))
                    if amp_value < 1e10:
                        current_amps.append(amp_value)
                except:
                    continue
                time.sleep(0.1)

            if not current_amps:
                raise ValueError("无法获取当前幅度")

            current_amp = sum(current_amps) / len(current_amps)

            if current_amp > target_amp:
                low = mid
            else:
                high = mid

        return round((low + high) / 2 * gain * 1e-6, 4)  # 转换为MHz
    except Exception as e:
        print(f"测量GBW时出错: {e}")
        return None
    finally:
        signal_generator.write(":OUTP1 OFF")


def measure_sr(power_supply, signal_generator, oscilloscope, vcc: float, amp_sr: float) -> Tuple[
    Optional[float], Optional[float]]:
    """测量压摆率"""
    try:
        # 电源设置
        power_supply.write(f":SOUR1:VOLT {vcc / 2};:CURR 0.1")
        power_supply.write(f":SOUR2:VOLT {vcc / 2};:CURR 0.1")
        power_supply.write(":OUTP CH1,ON;:OUTP CH2,ON;:OUTP CH3,OFF")
        time.sleep(1)

        # 信号发生器设置
        signal_generator.write(f":SOUR1:APPL:SQU 1000,{amp_sr},0,0")
        signal_generator.write(":OUTP1 ON")
        time.sleep(1)

        # 示波器设置
        oscilloscope.write(":AUToscale")
        time.sleep(3)

        # 测量压摆率
        pslewrates, nslewrates = [], []
        for _ in range(20):
            try:
                pslew = float(oscilloscope.query(":MEAS:ITEM? PSLewrate,CHAN2")) * 1e-6
                nslew = float(oscilloscope.query(":MEAS:ITEM? NSLewrate,CHAN2")) * 1e-6
                pslewrates.append(pslew)
                nslewrates.append(nslew)
            except:
                continue
            time.sleep(0.01)

        if not pslewrates or not nslewrates:
            raise ValueError("无法获取有效压摆率数据")

        return (round(sum(pslewrates) / len(pslewrates), 4),
                round(sum(nslewrates) / len(nslewrates), 4))
    except Exception as e:
        print(f"测量SR时出错: {e}")
        return None, None
    finally:
        signal_generator.write(":OUTP1 OFF")


def main():
    """主测试程序"""
    print("=" * 50)
    print("GBW和SR测试系统")
    print("=" * 50)

    # 用户配置
    enable_temp = input("启用温度测试? (y/n): ").strip().lower() == 'y'
    temperatures = [ 25,  -40, 125, 85] if enable_temp else [25]
    vcc_amp_pairs = [(5,1),(36,20)]
    gain = 11
    input_amp = 50

    # 结果存储
    results_gbw = []
    results_sr = []

    try:
        # 初始化仪器连接
        print("\n初始化仪器连接...")
        power_supply = rm.open_resource(url_DP832_0)
        signal_generator = rm.open_resource(url_DG832_0)
        oscilloscope = rm.open_resource(url_MSO5000)

        # 设置超时
        for instr in [power_supply, signal_generator, oscilloscope]:
            instr.timeout = 10000

        # 开始测试
        for temp in temperatures:
            print(f"\n当前温度: {temp}°C")

            for vcc, amp_sr in vcc_amp_pairs:
                print(f"正在测试 {vcc}V 条件...")

                # GBW测试
                gbw = measure_gbw(power_supply, signal_generator, oscilloscope, vcc, input_amp, gain)
                if gbw is not None:
                    print(f"GBW: {gbw} MHz")
                    results_gbw.append([temp, vcc, gbw])

                # SR测试
                pslew, nslew = measure_sr(power_supply, signal_generator, oscilloscope, vcc, amp_sr)
                if pslew is not None and nslew is not None:
                    print(f"正SR: {pslew} V/μs, 负SR: {nslew} V/μs")
                    results_sr.append([temp, vcc, pslew, nslew])

        # 保存结果
        if results_gbw or results_sr:
            save_to_excel(results_gbw, results_sr)

    except Exception as e:
        print(f"\n测试过程中发生严重错误: {e}")
    finally:
        # 清理资源
        print("\n正在清理资源...")
        try:
            power_supply.write(":OUTP CH1,OFF;:OUTP CH2,OFF;:OUTP CH3,OFF")
            power_supply.close()
        except:
            pass

        try:
            signal_generator.write(":OUTP1 OFF")
            signal_generator.close()
        except:
            pass

        try:
            oscilloscope.close()
        except:
            pass

        print("测试完成")


if __name__ == "__main__":
    # 安装必要库: pip install pyvisa pandas pywin32 pyserial openpyxl
    main()