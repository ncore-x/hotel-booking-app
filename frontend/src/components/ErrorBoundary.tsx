import { Component, type ReactNode } from "react";
import { Card } from "./ui/Card";
import { Button } from "./ui/Button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[50vh] items-center justify-center">
          <Card className="max-w-md text-center">
            <h2 className="mb-2 text-xl font-bold text-gray-900 dark:text-white">
              Что-то пошло не так
            </h2>
            <p className="mb-4 text-gray-500 dark:text-gray-400">
              Произошла непредвиденная ошибка
            </p>
            <Button onClick={() => window.location.reload()}>
              Перезагрузить
            </Button>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
