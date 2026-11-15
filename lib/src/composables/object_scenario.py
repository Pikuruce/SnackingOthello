from typing import Callable
import math
from lib.src.components.object import Object

def movePosition(
    target_vector: list[tuple[float, float, float]],
    ring: bool = False,
    loop: bool = False,
    speed: float = 1.0,
) -> Callable[[Object, float], Callable | None]:
    """
    オブジェクトに個別でセットするための関数を返す関数

    目的地点を周回させるための関数を返す
    """
    if not target_vector:
        raise ValueError("target_vector must not be empty")
    if speed <= 0:
        raise ValueError("speed must be greater than 0")

    # 移動状態を、この関数専用に保持する
    points = None
    target_index = 1
    direction = 1
    stop = False

    def restart() -> None:
        nonlocal stop
        stop = False

    def func(target: Object, dt: float) -> Callable | None:
        nonlocal points, target_index, direction, stop

        if stop:
            return restart
        
        # 初回実行時に、初期位置と各目的地を計算する
        if points is None:
            if target.init_pos is None:
                raise ValueError(
                    "init_pos must be set before using moveAround"
                )

            start = target.init_pos
            current = (start.x, start.y, start.z)
            points = [current]

            for x, y, z in target_vector:
                current = (
                    current[0] + x,
                    current[1] + y,
                    current[2] + z,
                )
                points.append(current)

        # 現在位置と目的地
        pos = target.getPos()
        destination = points[target_index]

        dx = destination[0] - pos.x
        dy = destination[1] - pos.y
        dz = destination[2] - pos.z

        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        step = speed * dt

        # 目的地に到着、または通り過ぎる場合
        if distance <= step or distance < 1e-6:
            target.setPos(
                destination[0],
                destination[1],
                destination[2],
            )

            # 次の目的地を決める
            if ring:
                # 最後の地点まで来たら初期位置へ戻る
                target_index = (
                    0
                    if target_index == len(points) - 1
                    else target_index + 1
                )
                if target_index == 1 and not loop:
                    stop = True
            else:
                # 端まで来たら進行方向を反転する
                if target_index == len(points) - 1:
                    direction = -1
                elif target_index == 0:
                    if not loop:
                        stop = True
                    direction = 1

                target_index += direction

        else:
            # 目的地に向かって一定速度で移動する
            ratio = step / distance

            target.setPos(
                pos.x + dx * ratio,
                pos.y + dy * ratio,
                pos.z + dz * ratio,
            )

    return func


def moveRotation(
    target_vector: list[tuple[float, float, float]],
    loop: bool = False,
    speed: float = 1.0,
) -> Callable[[Object, float], Callable | None]:
    """
    設定された回転動作をこなす関数を返す
    """

    if not target_vector:
        raise ValueError("target_vector must not be empty")
    if speed <= 0:
        raise ValueError("speed must be greater than 0")

    points = None
    target_index = 1
    direction = 1
    stop = False

    def restart() -> None:
        nonlocal stop
        stop = False

    def func(target: Object, dt: float) -> Callable | None:
        nonlocal points, target_index, direction, stop

        if stop:
            return restart

        # 初回実行時に初期位置と目的地を計算
        if points is None:
            start = target.getRotate()
            current = tuple(start)
            points = [current]

            for x, y, z in target_vector:
                current = (
                    current[0] + x,
                    current[1] + y,
                    current[2] + z,
                )
                points.append(current)

        # 現在位置と目的地
        rotate = target.getRotate()
        destination = points[target_index]

        dh = destination[0] - rotate[0]
        dp = destination[1] - rotate[1]
        dr = destination[2] - rotate[2]

        distance = math.sqrt(dh * dh + dp * dp + dr * dr)
        step = speed * dt

        # 目的地に到着、または通り過ぎる場合
        if distance <= step or distance < 1e-6:
            target.setRotate(*destination)

            # 端まで来たら進行方向を反転
            if target_index == len(points) - 1:
                if not loop:
                    stop = True
                direction = -1
            elif target_index == 0:
                if not loop:
                    stop = True
                direction = 1

            target_index += direction

        else:
            # 目的地に向かって一定速度で回転
            ratio = step / distance

            target.setRotate(
                rotate[0] + dh * ratio,
                rotate[1] + dp * ratio,
                rotate[2] + dr * ratio,
            )

    return func