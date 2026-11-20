CREATE OR REPLACE FUNCTION public.fn_data_atualizacao()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pedido_data_atualizacao
BEFORE UPDATE ON public.pedido
FOR EACH ROW
EXECUTE FUNCTION public.fn_data_atualizacao();

CREATE TRIGGER trg_item_pedido_data_atualizacao
BEFORE UPDATE ON public.item_pedido
FOR EACH ROW
EXECUTE FUNCTION public.fn_data_atualizacao();