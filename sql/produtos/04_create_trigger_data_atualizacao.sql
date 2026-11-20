CREATE OR REPLACE FUNCTION public.fn_data_atualizacao()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_produto_data_atualizacao
BEFORE UPDATE ON public.produto
FOR EACH ROW
EXECUTE FUNCTION public.fn_data_atualizacao();