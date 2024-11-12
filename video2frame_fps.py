__author__ = 'vfdev'

import argparse
import os
import shutil
import subprocess
import json
import cv2
import math
from glob import glob
from tqdm import tqdm

# 内置默认参数
DEFAULT_ARGS = {
    'input': '/data/jj/datasets/video/websurg',  # 输入视频文件夹路径
    'output': '/data/jj/datasets/frames/frames_original/websurg',  # 输出帧文件夹路径
    'maxframes': None,    # 最大帧数，None表示不限制
    'rotate': None,       # 旋转角度，可选值：90, 180, 270
    'exifmodel': None,    # EXIF模板文件
    'verbose': True,      # 是否显示详细信息
    'target_fps': None    # 目标fps，None表示使用原始fps
}

def process_video(video_path, output_base_path, args):
    """处理单个视频文件"""
    # 获取视频文件名（不含扩展名）作为输出子文件夹名
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_base_path, video_name)
    
    if args.verbose:
        print(f"\n处理视频: {video_path}")
        print(f"输出目录: {output_path}")

    if os.path.exists(output_path):
        if args.verbose:
            print(f"移除已存在的输出文件夹: {output_path}")
        shutil.rmtree(output_path)

    os.makedirs(output_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"错误：无法打开视频 {video_path}")
        return 1

    original_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration = frame_count / original_fps  # 视频总时长（秒）

    if args.verbose:
        print(f"原始FPS: {original_fps}")
        print(f"总帧数：{frame_count}")
        print(f"视频时长：{video_duration:.2f}秒")

    # 计算实际使用的FPS
    target_fps = args.target_fps if args.target_fps else original_fps
    
    if args.verbose and args.target_fps:
        print(f"目标FPS: {target_fps}")

    # 计算需要提取的总帧数
    target_frame_count = int(video_duration * target_fps)
    
    # 如果设置了maxframes，调整目标帧数
    if args.maxframes and target_frame_count > args.maxframes:
        target_frame_count = args.maxframes
        if args.verbose:
            print(f"由于maxframes限制，实际输出帧数将为: {target_frame_count}")
    
    # 计算帧间隔（在原始视频帧的基础上）
    frame_interval = frame_count / target_frame_count
    
    if args.verbose:
        print(f"帧间隔: {frame_interval:.2f}")

    frame_id = 0  # 原始视频的帧索引
    output_frame_count = 0  # 输出的帧计数

    # 创建进度条
    pbar = tqdm(total=target_frame_count, desc="处理帧", unit="帧")

    while frame_id < frame_count:
        ret, frame = cap.read()
        if not ret:
            print(f"无法获取帧 {frame_id}")
            continue

        # 计算当前时间戳（秒）
        current_second = frame_id / original_fps
        
        # 旋转帧（如果需要）
        if args.rotate:
            if args.rotate == 90:
                frame = cv2.transpose(frame)
                frame = cv2.flip(frame, 1)
            elif args.rotate == 180:
                frame = cv2.flip(frame, -1)
            elif args.rotate == 270:
                frame = cv2.transpose(frame)
                frame = cv2.flip(frame, 0)

        # 保存帧，使用时间戳作为文件名
        timestamp = f"{current_second:.3f}"  # 保留3位小数的秒数
        fname = f"{timestamp}.jpg"
        ofname = os.path.join(output_path, fname)
        ret = cv2.imwrite(ofname, frame)
        if not ret:
            print(f"无法写入帧 {timestamp}")
            continue

        output_frame_count += 1
        # 计算下一帧的位置
        frame_id = int(output_frame_count * frame_interval)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

        # 更新进度条
        pbar.update(1)

        if args.maxframes and output_frame_count >= args.maxframes:
            break

    cap.release()
    pbar.close()
    
    if args.verbose:
        print(f"处理完成，共输出 {output_frame_count} 帧")
    return 0

def main(args):
    if args.verbose:
        print("Input arguments:", args)

    input_path = args.input or DEFAULT_ARGS['input']
    output_path = args.output or DEFAULT_ARGS['output']
    
    if not os.path.exists(input_path):
        print(f"错误：输入路径不存在 - {input_path}")
        return 1

    # 确保输出根目录存在
    os.makedirs(output_path, exist_ok=True)

    # 修改视频文件获取逻辑
    if os.path.isfile(input_path):
        # 如果输入是单个文件
        video_files = [input_path]
    else:
        # 如果输入是目录
        video_files = glob(os.path.join(input_path, "*.mp4"))
    
    if not video_files:
        print(f"错误：没有找到视频文件")
        return 1

    print(f"找到 {len(video_files)} 个视频文件")

    # 处理每个视频文件
    for i, video_file in enumerate(video_files, 1):
        print(f"\n处理第 {i}/{len(video_files)} 个视频文件")
        process_video(video_file, output_path, args)

    print("\n所有视频处理完成！")
    return 0

if __name__ == "__main__":
    print("开始批量视频转帧处理...")

    parser = argparse.ArgumentParser(description="批量视频转帧工具")
    parser.add_argument('--input', help="输入视频文件夹路径")
    parser.add_argument('--output', help="输出文件夹路径")
    parser.add_argument('--maxframes', type=int, help="每个视频的最大输出帧数")
    parser.add_argument('--rotate', type=int, choices={90, 180, 270}, help="顺时针旋转角度")
    parser.add_argument('--exifmodel', help="用于填充输出元标签的示例照片文件")
    parser.add_argument('--verbose', action='store_true', help="显示详细信息")
    parser.add_argument('--target_fps', type=float, help="目标FPS，不设置则使用原始FPS")

    args = parser.parse_args()
    
    if not any(vars(args).values()):
        print("使用默认参数...")
        args.input = DEFAULT_ARGS['input']
        args.output = DEFAULT_ARGS['output']
        args.maxframes = DEFAULT_ARGS['maxframes']
        args.rotate = DEFAULT_ARGS['rotate']
        args.exifmodel = DEFAULT_ARGS['exifmodel']
        args.verbose = DEFAULT_ARGS['verbose']
        args.target_fps = DEFAULT_ARGS['target_fps']

    ret = main(args)
    exit(ret)